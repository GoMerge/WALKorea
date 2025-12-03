from app.models.place import Place
from app.models.user_profile import UserProfile
from sqlalchemy import or_
from sqlalchemy.orm import Session

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
    
