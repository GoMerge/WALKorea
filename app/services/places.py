import requests
from sqlalchemy.orm import Session
from fastapi import HTTPException
from app.models.places import Place, PlaceDetail, PlaceImage, Festival

TOUR_API_BASE = "http://apis.data.go.kr/B551011/KorService2"
SERVICE_KEY = "07b00c849181aa6c2bbdfbce284aff0ce01778ccc5e6a1fb9e9d49cad24ba714"

def fetch_tour_data(page: int = 1, num_of_rows: int = 10):
    url = f"{TOUR_API_BASE}/areaBasedList2"
    params = {
        "MobileOS": "ETC",
        "MobileApp": "WALKorea",
        "_type": "json",
        "numOfRows": num_of_rows,
        "pageNo": page,
        "serviceKey": SERVICE_KEY,
        "arrange": "A",
    }
    res = requests.get(url, params=params)
    res.raise_for_status()
    data = res.json()
    items = data["response"]["body"]["items"]["item"]
    if not isinstance(items, list):
        items = [items]
    return items


def save_places_to_db(db: Session, page: int = 1):
    items = fetch_tour_data(page)
    for i in items:
    # DB에 이미 존재하면 skip
        existing = db.query(Place).filter(Place.content_id == str(i["contentid"])).first()
        if not existing:
            place = Place(
            content_id=str(i["contentid"]),
            content_type_id=i.get("contenttypeid", 0),
            title=i.get("title", ""),
            addr1=i.get("addr1"),
            addr2=i.get("addr2"),
            areacode=i.get("areacode"),
            sigungucode=i.get("sigungucode"),
            latitude=float(i.get("mapy")) if i.get("mapy") else None,
            longitude=float(i.get("mapx")) if i.get("mapx") else None,
            overview=i.get("overview", ""),
        )
        db.add(place)
    db.commit()


def get_all_places(db: Session, page: int = 1, per_page: int = 10):
    offset = (page - 1) * per_page
    return db.query(Place).order_by(Place.id.desc()).offset(offset).limit(per_page).all()

def get_all_places(db: Session, page: int = 1, per_page: int = 10, keyword: str = None):
    query = db.query(Place)
    if keyword:
        query = query.filter(Place.title.contains(keyword))
    offset = (page - 1) * per_page
    return query.order_by(Place.id.desc()).offset(offset).limit(per_page).all()

def get_place_detail(db: Session, content_id: str):
    # 1. DB에서 조회
    detail = db.query(PlaceDetail).filter_by(place_id=content_id).first()
    if detail:
        return detail

    # 2. DB에 없으면 TourAPI 호출/파싱
    url = f"{TOUR_API_BASE}/detailCommon2"
    params = {
        "MobileOS": "ETC",
        "MobileApp": "WALKorea",
        "_type": "json",
        "contentId": content_id,
        "serviceKey": SERVICE_KEY,
        # "defaultYN": "Y",    # 반드시 제거!
        # "overviewYN": "Y",  # 문서에 없으므로 제거 (필요 시 docs에서 지원 여부 확인)
        # "firstImageYN": "Y",# 반드시 제거!
        # "addrinfoYN": "Y",  # 반드시 제거!
    }

    try:
        res = requests.get(url, params=params)
        res.raise_for_status()
        res_json = res.json()
        print("API raw 응답 구조:", res_json)
        data = (res_json.get("response", {})
                         .get("body", {})
                         .get("items", {})
                         .get("item"))
        if not data:
            raise HTTPException(404, detail="상세 데이터 없음 (API item 없음)")
        if isinstance(data, list):
            data = data[0] if data else None
        if not data:
            raise HTTPException(404, detail="상세 데이터 없음 (item 내부 구조문제)")
    except Exception as e:
        print("API 예외 발생:", e)
        raise HTTPException(500, detail=f"TourAPI 호출/파싱 에러: {str(e)}")

    # 3. DB에 저장 후 반환
    detail = PlaceDetail(
        place_id=content_id,
        detail_json=data
    )
    db.add(detail)
    db.commit()
    db.refresh(detail)
    return detail
