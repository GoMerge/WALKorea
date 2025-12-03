# app/services/hashtag.py

from collections import Counter
from konlpy.tag import Okt
from sqlalchemy.orm import Session

from app.database import get_db

from app.models.hashtag import Tag, PlaceTag
from app.models.places import Place
from app.services.places import save_places_to_db

okt = Okt()

# ------------------------------------------
# 기본 관광 타입 기반 해시태그
# ------------------------------------------
CONTENT_TYPE_HASHTAGS = {
    12: ["여행", "가족"],
    14: ["문화", "체험"],
    15: ["축제", "공연"],
    25: ["코스", "트래킹"],
    28: ["레포츠", "액티비티"],
    32: ["숙박", "호텔"],
    38: ["쇼핑", "기념품"],
    39: ["맛집", "음식"]
}

# 계절 / 테마 키워드
SEASON_KEYWORDS = {
    "겨울": "#겨울여행",
    "봄": "#봄여행",
    "여름": "#여름여행",
    "가을": "#가을여행",
    "바다": "#바다",
    "산": "#산",
    "호수": "#호수",
    "산책로": "#산책로"
}

# 불용어
STOPWORDS = ["관광지", "장소", "소개", "대한", "여행", "지역", "한번", "정도"]


# ------------------------------------------
# 1. 키워드 추출
# ------------------------------------------
def extract_keywords(text: str, top_n: int = 5):
    nouns = okt.nouns(text)
    filtered = [word for word in nouns if len(word) > 1 and word not in STOPWORDS]
    freq = Counter(filtered)
    return [word for word, _ in freq.most_common(top_n)]

# ------------------------------------------
# 2. DB에서 모든 태그 캐시 로딩
# ------------------------------------------
def load_all_tags(db: Session):
    tags = db.query(Tag).all()
    return {tag.name: tag for tag in tags}

# ------------------------------------------
# 2. 특정 Place에 대해 해시태그 생성
# ------------------------------------------
def generate_hashtags_fast(db: Session, place_id: int, tag_cache: dict):
    place = db.query(Place).filter(Place.id == place_id).first()
    if not place:
        return []

    hashtags = set()

    # 1) 관광 타입 기반 기본 태그
    #content_tags = CONTENT_TYPE_HASHTAGS.get(place.contenttypeid, [])
    #hashtags.update(content_tags)
    hashtags.update(CONTENT_TYPE_HASHTAGS.get(place.contenttypeid, []))


    # 2) overview 기반 주요 키워드
    if place.overview:
        keywords = extract_keywords(place.overview)
        #주소관련 해시태그 생성금지
        if place.addr1:
            addr_words = set(extract_keywords(place.addr1))
            keywords = [kw for kw in keywords if kw not in addr_words]
        hashtags.update(keywords)

    # 3) 계절/테마 태그 (overview에 특정 키워드 포함 시)
    if place.overview:
        overview_text = place.overview.lower()
        for key, tag in SEASON_KEYWORDS.items():
            if key in place.overview:
                hashtags.add(tag.lstrip("#"))

    # 기존 PlaceTag 조회
    existing = db.query(PlaceTag).filter(PlaceTag.place_id == place_id).all()
    existing_tag_ids = {pt.tag_id for pt in existing}

    results = []

    for name in hashtags:
        if name in tag_cache:
            tag = tag_cache[name]
        else:
            tag = Tag(name=name, slug=name.lower())
            db.add(tag)
            db.flush()
            tag_cache[name] = tag

        if tag.id not in existing_tag_ids:
            db.add(PlaceTag(place_id=place_id, tag_id=tag.id))

        results.append(f"#{name}")

    return results


# ------------------------------------------
# 3. 해시태그 기반 장소 검색
# ------------------------------------------
def search_places_by_hashtag(db: Session, hashtag: str):
    tag = db.query(Tag).filter(Tag.slug == hashtag.lower()).first()
    if not tag:
        return []

    place_ids = [pt.place_id for pt in tag.places]
    return db.query(Place).filter(Place.id.in_(place_ids)).all()


# ------------------------------------------
# 4. DB 저장 + 해시태그 생성 (API용)
# -----------------------------------------
def generate_hashtags_for_all_saved_places_service(db: Session, batch_size: int = 1000):
    places = db.query(Place).all()
    tag_cache = load_all_tags(db)
    total_tags_generated = 0

    for i in range(0, len(places), batch_size):
        batch = places[i:i + batch_size]
        for place in batch:
            tags = generate_hashtags_fast(db, place.id, tag_cache)
            total_tags_generated += len(tags)
        db.commit()  # 배치 단위 commit → 안정성 증가
        print(f"[진행 상황] {i + len(batch)} / {len(places)} Place 처리 완료, 총 해시태그 생성: {total_tags_generated}")

    return {
        "message": "고속 배치 해시태그 생성 완료!",
        "num_of_places": len(places),
        "total_hashtags_created": total_tags_generated,
    }