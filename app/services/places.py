from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session, joinedload
from app.database import get_db
import requests
from sqlalchemy.orm import Session
from app.models.places import Place, PlaceDetail
from app.models.hashtag import PlaceTag, Tag
import math
from fastapi.templating import Jinja2Templates
import os


TOUR_API_BASE = "http://apis.data.go.kr/B551011/KorService2"

SERVICE_KEY = os.getenv("SERVICE_KEY")

MAX_SAVE_COUNT = 30000  # DB에 저장할 최대 관광지 개수

# ------------------------------------------
# 1️⃣ TourAPI - 관광지 목록(areaBasedList2) 가져오기
# ------------------------------------------
def fetch_tour_data(page: int = 1, num_of_rows: int = 100):
    url = f"{TOUR_API_BASE}/areaBasedList2"
    params = {
        "MobileOS": "ETC",
        "MobileApp": "WALKorea",
        "_type": "json",
        "numOfRows": num_of_rows,
        "pageNo": page,
        "serviceKey": SERVICE_KEY,
        "arrange": "C",
    }
    res = requests.get(url, params=params)
    res.raise_for_status()
    data = res.json()
    
    items = data["response"]["body"]["items"]["item"]
    # item이 단일 dict이면 리스트로 감싸기
    if not isinstance(items, list):
        items = [items]
    return items

# ------------------------------------------
# 2️⃣ TourAPI - 관광지 상세정보(detailCommon2) 가져오기
# ------------------------------------------
def fetch_place_detail(contentid: str) -> dict:
    """
    TourAPI detailCommon2 호출
    overview, firstimage, homepage 등 상세정보 포함
    """
    url = f"{TOUR_API_BASE}/detailCommon2"
    params = {
        "MobileOS": "ETC",
        "MobileApp": "WALKorea",
        "_type": "json",
        "contentId": contentid,
        "serviceKey": SERVICE_KEY,
    }

    res = requests.get(url, params=params)
    res.raise_for_status()
    item = res.json()["response"]["body"]["items"]["item"]

    if isinstance(item, list):
        return item[0]
    return item


# ------------------------------------------
# 3️⃣ DB 저장 - 최대 30,000개
# ------------------------------------------
def save_places_to_db(db: Session, num_of_rows: int = 1000, max_pages: int = 1000):
    """
    areaBasedList2에서 목록을 가져와
    detailCommon2 상세정보까지 포함해 DB에 저장
    최대 30,000개까지만 저장
    """
    page = 1
    saved_count = db.query(Place).count()  # 이미 저장된 개수 확인

    print(f"현재 DB 저장 개수: {saved_count}개")

    while page <= max_pages:
        # 최대 30,000개 저장 도달 시 종료
        if saved_count >= MAX_SAVE_COUNT:
            print("📌 최대 30,000개 저장 완료 → 종료")
            break

        items = fetch_tour_data(page, num_of_rows=num_of_rows)

        if not items:
            print(f"⚠ 페이지 {page}에서 데이터 없음 → 종료")
            break

        # 페이지별 처리 로그
        print(f"📄 {page} 페이지 처리 중... (총 {saved_count}개)")

        for i in items:
            if saved_count >= MAX_SAVE_COUNT:
                break

            contentid = str(i["contentid"])

            # 중복 체크
            existing = db.query(Place).filter(Place.contentid == contentid).first()
            if existing:
                continue

            # 상세정보 가져오기
            detail = fetch_place_detail(contentid)

            # Place 저장
            place = Place(
                contentid=contentid,
                contenttypeid=i.get("contenttypeid", 0),
                title=i.get("title", ""),
                addr1=i.get("addr1", ""),
                addr2=i.get("addr2", ""),
                areacode=i.get("areacode"),
                sigungucode=i.get("sigungucode"),
                mapx=float(i.get("mapx")) if i.get("mapx") else None,
                mapy=float(i.get("mapy")) if i.get("mapy") else None,
                cat1=i.get("cat1", ""),
                cat2=i.get("cat2", ""),
                cat3=i.get("cat3", ""),
                overview=detail.get("overview", ""),
                firstimage=detail.get("firstimage", ""),
                firstimage2=detail.get("firstimage2", ""),
                homepage=detail.get("homepage", ""),
                tel=detail.get("tel", ""),
                zipcode=detail.get("zipcode", ""),
            )
            db.add(place)


            saved_count += 1

        db.commit()
        page += 1

    print(f"🎉 최종 저장 개수: {saved_count}개")


# ✅ 상세정보 조회 (DB에 없으면 TourAPI 호출 후 저장)
def get_place_detail(db: Session, contentid: str):
    detail = db.query(PlaceDetail).filter_by(place_id=contentid).first()
    if detail:
        return detail

    # DB에 없으면 TourAPI 호출
    url = f"{TOUR_API_BASE}/detailCommon2"
    params = {
        "MobileOS": "ETC",
        "MobileApp": "WALKorea",
        "_type": "json",
        "contentId": contentid,
        "serviceKey": SERVICE_KEY,
    }
    res = requests.get(url, params=params)
    res.raise_for_status()
    data = res.json()["response"]["body"]["items"]["item"][0]

    # DB에 저장
    detail = PlaceDetail(
        place_id=contentid,
        detail_json=data
    )
    db.add(detail)
    db.commit()
    db.refresh(detail)
    return detail

#--------------------------------------------------------------------------------------------------
# 리스트 템플릿 연동
#--------------------------------------------------------------------------------------------------


def get_places_page(db: Session, page: int = 1, per_page: int = 10):
    offset = (page - 1) * per_page
    total = db.query(Place).count()
    total_pages = (total + per_page - 1) // per_page
    places = (
        db.query(Place)
        .options(joinedload(Place.hashtags).joinedload(PlaceTag.tag))
        .order_by(Place.id.desc())
        .offset(offset)
        .limit(per_page)
        .all()
    )
    return places, total_pages