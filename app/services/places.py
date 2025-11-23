import requests
from sqlalchemy.orm import Session
from app.models.places import Place, PlaceDetail, PlaceImage, Festival

TOUR_API_BASE = "http://apis.data.go.kr/B551011/KorService2"
SERVICE_KEY = "07b00c849181aa6c2bbdfbce284aff0ce01778ccc5e6a1fb9e9d49cad24ba714"

# ✅ TourAPI에서 관광지 목록 가져오기
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


# ✅ DB에 저장
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


# ✅ DB에서 모든 관광지 조회
def get_all_places(db: Session, page: int = 1, per_page: int = 10):
    offset = (page - 1) * per_page
    return db.query(Place).order_by(Place.id.desc()).offset(offset).limit(per_page).all()

def get_all_places(db: Session, page: int = 1, per_page: int = 10, keyword: str = None):
    query = db.query(Place)
    if keyword:
        query = query.filter(Place.title.contains(keyword))
    offset = (page - 1) * per_page
    return query.order_by(Place.id.desc()).offset(offset).limit(per_page).all()

# ✅ 상세정보 조회 (DB에 없으면 TourAPI 호출 후 저장)
def get_place_detail(db: Session, content_id: str):
    detail = db.query(PlaceDetail).filter_by(place_id=content_id).first()
    if detail:
        return detail

    # DB에 없으면 TourAPI 호출
    url = f"{TOUR_API_BASE}/detailCommon2"
    params = {
        "MobileOS": "ETC",
        "MobileApp": "WALKorea",
        "_type": "json",
        "contentId": content_id,
        "defaultYN": "Y",
        "overviewYN": "Y",
        "addrinfoYN": "Y",
        "firstImageYN": "Y",
        "serviceKey": SERVICE_KEY,
    }
    res = requests.get(url, params=params)
    res.raise_for_status()
    data = res.json()["response"]["body"]["items"]["item"][0]

    # DB에 저장
    detail = PlaceDetail(
        place_id=content_id,
        detail_json=data
    )
    db.add(detail)
    db.commit()
    db.refresh(detail)
    return detail