from app.models.places import Place
from app.models.user_profile import UserProfile
from sqlalchemy import or_
from sqlalchemy.orm import Session
from typing import List, Dict, Tuple

USER_TOP_RECOMMENDED: dict[int, set[int]] = {}
TOP_N = 12

def recommend_places_for_user(db: Session, user_id: int):
    user_pref = db.query(UserProfile).filter_by(user_id=user_id).first()
    if not user_pref:
        return db.query(Place).order_by(Place.id.desc()).limit(10).all()  # 기본 추천

    # preferences에서 키워드 추출 (예: 리스트/값 flatten)
    pref = user_pref.preferences

    tags_to_match = []
    for key, value in pref.items():
        if isinstance(value, list):
            tags_to_match += value
        elif isinstance(value, str) and value != "알 수 없음" and value != "보통":
            tags_to_match.append(value)
        elif isinstance(value, bool) and value:
            tags_to_match.append(key)
    
    # 주요 키워드(태그/설명)와 매칭
    query = db.query(Place)
    condition = []
    for tag in tags_to_match:
        # 태그 및 상세설명 모두 검색
        condition.append(Place.tags.ilike(f"%{tag}%"))  # tags: 태그 문자열 or json list 필드
        condition.append(Place.description.ilike(f"%{tag}%"))
    # OR 조건 매칭이 높은 순으로 정렬, 그 외 일반적인 인기순/최신순 fallback
    places = query.filter(or_(*condition)).order_by(Place.id.desc()).all()
    return places[:20]  # 최상위 20개 등
    
def score_place_by_preferences(place: Place, prefs: dict) -> dict:

    pk = extract_place_keywords(place)

    # 1) 기본 정보 (나이대/성별/동행자 타입 등 기반으로 키 하나 선정)
    user_basic = prefs.get("companion")  # 예: '혼자', '연인', '가족'
    place_basic_vals = pk["tags"]  # 해시태그로 동행자 친화 여부 표현되어 있다고 가정
    base_raw = three_level_match(user_basic, place_basic_vals)

    # 2) 여행 취향 (산/바다/도시, 활동 타입)
    user_area = prefs.get("area_theme")        # str 또는 list
    area_raw = three_level_match(user_area, pk["area"])

    user_activity = prefs.get("activity_type") # str 또는 list
    act_raw = three_level_match(user_activity, pk["activity"])

    user_vibe = prefs.get("situation")        # str 또는 list
    distance_raw = three_level_match(user_vibe, pk["vibe"])

    topic_raw = (area_raw + act_raw) / 2

    # 가중합으로 최종 점수
    total_raw = (
        base_raw * 0.2 +
        topic_raw * 0.5 +
        distance_raw * 0.3
    )

    return {
        "base": base_raw,
        "topic": topic_raw,
        "distance": distance_raw,
        "total": total_raw,
    }


def sort_places_with_preferences(
    db: Session, user_id: int, places: List[Place]
) -> Tuple[List[Place], str | None, Dict[int, dict]]:

    print(">>> sort_places_with_preferences called, user_id =", user_id, "places:", len(places))

    profile = db.query(UserProfile).filter(UserProfile.user_id == user_id).first()
    if not profile or not profile.preferences:
        # 점수 정보가 없으면 원래 리스트 그대로, 점수맵은 빈 dict
        return places, None, {}

    prefs: dict = profile.preferences

    scored: list[tuple[float, Place, dict]] = []
    for p in places:
        detail_scores = score_place_by_preferences(p, prefs)
        total_score = detail_scores["total"]
        scored.append((total_score, p, detail_scores))

    scored.sort(key=lambda x: x[0], reverse=True)
    sorted_places: List[Place] = [p for _, p, _ in scored]

    score_map: Dict[int, dict] = {
        p.contentid: detail for _, p, detail in scored
    }

    summary = ", ".join(prefs.get("area_theme", [])) or prefs.get("vibe") or ""
    return sorted_places, summary, score_map

def get_place_scores_for_user(
    db: Session, user_id: int, place_id: int
) -> dict | None:
    top_ids = USER_TOP_RECOMMENDED.get(user_id)
    if not top_ids:
        print("NO TOP12", user_id, top_ids)
        return None

    # ★ place_id 도 int 로 맞춰서 비교
    pid = int(place_id)
    if pid not in top_ids:
        print("NOT IN TOP12", user_id, pid, top_ids)
        return None

    profile = db.query(UserProfile).filter(UserProfile.user_id == user_id).first()
    if not profile or not profile.preferences:
        print("NO PROFILE/PREFS", user_id)
        return None

    place = db.query(Place).filter(Place.contentid == pid).first()
    if not place:
        print("NO PLACE", pid)
        return None

    scores = score_place_by_preferences(place, profile.preferences)
    print("DETAIL SCORE FOR", user_id, pid, scores)
    return scores


def three_level_match(user_value, place_values: list[str]) -> float:
    
    # 1) 리스트인 경우: 여러 선호값 중 하나라도 잘 맞으면 높은 점수
    if isinstance(user_value, (list, tuple, set)):
        if not user_value:
            return 0.5
        scores = [three_level_match(v, place_values) for v in user_value]
        return max(scores)  # 가장 잘 맞는 것을 사용

    # 2) 여기부터는 user_value 가 str 이라고 가정
    if not user_value or user_value in {"알 수 없음", "보통"}:
        return 0.5

    if not place_values:
        return 0.5

    if user_value in place_values:
        return 1.0

    opposite_map = {
        "산": "바다",
        "바다": "산",
        "도시": "자연",
        "자연": "도시",
    }
    opp = opposite_map.get(user_value)
    if opp and opp in place_values:
        return 0.0

    return 0.5


def extract_place_keywords(place: Place) -> dict:

    tags = [pt.tag.name for pt in getattr(place, "hashtags", [])]

    area_keywords: list[str] = []
    if place.addr1:
        if "산" in place.addr1:
            area_keywords.append("산")
        if "해수욕장" in place.addr1 or "해변" in place.addr1 or "바다" in place.addr1:
            area_keywords.append("바다")
        if any(word in place.addr1 for word in ["도심", "역", "광장"]):
            area_keywords.append("도시")

    # 활동 타입 예시: 음식점 / 카페 / 박물관 / 축제 등
    activity_keywords: list[str] = []
    if place.contenttypeid == 39:
        activity_keywords.append("맛집")
    if place.contenttypeid == 14:
        activity_keywords.append("문화")
    if place.contenttypeid == 15:
        activity_keywords.append("축제")

    # 해시태그도 영역/활동에 섞기
    for t in tags:
        if t in {"산", "바다", "도시", "자연"}:
            area_keywords.append(t)
        if t in {"맛집", "카페", "체험", "축제", "레포츠"}:
            activity_keywords.append(t)

    # 상황/거리: 예시는 '멀리 가기 싫음/상관 없음/당일치기' 등 선호와 비교할 것
    vibe_keywords: list[str] = []
    # 예시: 혼잡도/분위기에 대한 해시태그 있으면 여기서 추가

    return {
        "tags": tags,
        "area": area_keywords,
        "activity": activity_keywords,
        "vibe": vibe_keywords,
    }