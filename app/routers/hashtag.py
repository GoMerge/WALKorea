# app/routers/hashtag.py
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.database import get_db
from app.services.hashtag import (
    generate_hashtags_fast,
    search_places_by_hashtag,
    generate_hashtags_for_all_saved_places_service,
    load_all_tags
)

router = APIRouter(prefix="/hashtags", tags=["Hashtags"])

# 특정 Place에 해시태그 생성
@router.post("/generate/{place_id}")
def generate_place_hashtags(place_id: int, db: Session = Depends(get_db)):
    tag_cache = load_all_tags(db)
    hashtags = generate_hashtags_fast(db, place_id, tag_cache)
    db.commit()  # PlaceTag, Tag 모두 commit
    return {"place_id": place_id, "hashtags": hashtags}


# 해시태그 검색 → 관련 관광지 조회
@router.get("/search")
def search_by_hashtag(tag: str = Query(..., description="검색할 해시태그"), db: Session = Depends(get_db)):
    places = search_places_by_hashtag(db, tag)
    return {"hashtag": tag, "places": [{"id": p.id, "title": p.title} for p in places]}


# DB 저장 관광지 기준 해시태그 일괄 생성
@router.post("/places/fetch/all", summary="DB 저장 관광지 기준 해시태그 생성")
def generate_hashtags_for_all_saved_places(db: Session = Depends(get_db)):
    return generate_hashtags_for_all_saved_places_service(db)