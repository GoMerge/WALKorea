from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session, joinedload
from app.database import get_db
import requests
from app.models.places import Place, PlaceDetail
from app.models.hashtag import PlaceTag, Tag
from app.models.user import User
import math
from typing import List, Dict
import os
from app.services.recommendation_service import (
    sort_places_with_preferences,
)
from sqlalchemy import case, or_



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
# 이미지 불러오기
# ------------------------------------------
def fetch_detail_images(contentid: str) -> List[Dict[str, str]]:
    """
    TourAPI detailImage1 API 호출 - 썸네일 갤러리용 originimgurl 리스트
    """
    if not SERVICE_KEY:
        print("⚠️ SERVICE_KEY 환경변수 필요!")
        return []
    
    url = f"{TOUR_API_BASE}/detailImage2"  # detailImage1 endpoint
    params = {
        "serviceKey": SERVICE_KEY,
        "contentId": contentid,
        "MobileOS": "ETC",
        "MobileApp": "WALKorea",
        "imageYN": "Y",
        "_type": "json"
    }
    
    try:
        res = requests.get(url, params=params, timeout=10)
        res.raise_for_status()
        data = res.json()
        
        if data["response"]["header"]["resultCode"] == "0000":
            items = data["response"]["body"]["items"]["item"]
            if not isinstance(items, list):
                items = [items]
            
            # originimgurl만 추출 (중복 제거)
            images = []
            seen_urls = set()
            for item in items:
                url = item.get("originimgurl")
                if url and url not in seen_urls:
                    images.append({"originimgurl": url})
                    seen_urls.add(url)
                    if len(images) >= 12:  # 최대 12개만
                        break
            return images
        else:
            print(f"📡 이미지 API URL 요청: {url}")
            print(f"📡 응답 데이터: {data}")
            print(f"❌ TourAPI 이미지 에러: {data['response']['header']['resultMsg']}")
            return []
            
    except Exception as e:
        print(f"❌ 이미지 API 호출 실패: {e}")
        return []
    
    
# ------------------------------------------
# 디테일 정보2 가져오기
# ------------------------------------------
def fetch_detail_info(contentid: str, contenttypeid: str):
    try:
        url = f"{TOUR_API_BASE}/detailIntro2"

        params = {
            "MobileOS": "ETC",
            "MobileApp": "AppTest",
            "serviceKey": SERVICE_KEY,
            "contentId": contentid,
            "contentTypeId": contenttypeid,
            "_type": "json"
        }
        print("\n====== 📡 DETAIL INTRO2 요청 ======")
        print("URL:", url)
        print("Params:", params)

        print("📡 detailInfo2 URL:", url)

        response = requests.get(url, params=params)
        data = response.json()

        header = data["response"]["header"]
        result_code = header["resultCode"]

        if result_code not in ["0000", "000"]:
            print("❌ detailInfo2 에러:", header["resultMsg"])
            return None

        body = data["response"]["body"]
        items = body.get("items", {}).get("item", [])

        print("📡 detailInfo2 응답:", items)

        if not items:
            return None

        raw_item = items[0]  # detailIntro2는 1개만 반환

        # ---------------------------
        # ⭐ contentTypeId별 필드 정의
        # ---------------------------
        INFO_FIELDS = {
    "12": {  # 관광지
        "accomcount": "수용인원",
        "chkbabycarriage": "유모차대여정보",
        "chkcreditcard": "신용카드가능정보",
        "chkpet": "애완동물동반가능정보",
        "expagerange": "체험가능연령",
        "expguide": "체험안내",
        "heritage1": "세계문화유산유무",
        "heritage2": "세계자연유산유무",
        "heritage3": "세계기록유산유무",
        "infocenter": "문의및안내",
        "opendate": "개장일",
        "parking": "주차시설",
        "restdate": "쉬는날",
        "useseason": "이용시기",
        "usetime": "이용시간",
    },

    "14": {  # 문화시설
        "accomcountculture": "수용인원",
        "chkbabycarriageculture": "유모차대여정보",
        "chkcreditcardculture": "신용카드가능정보",
        "chkpetculture": "애완동물동반가능정보",
        "discountinfo": "할인정보",
        "infocenterculture": "문의및안내",
        "parkingculture": "주차시설",
        "parkingfee": "주차요금",
        "restdateculture": "쉬는날",
        "usefee": "이용요금",
        "usetimeculture": "이용시간",
        "scale": "규모",
        "spendtime": "관람소요시간",
    },

    "15": {  # 행사/공연/축제
        "agelimit": "관람가능연령",
        "bookingplace": "예매처",
        "discountinfofestival": "할인정보",
        "eventenddate": "행사종료일",
        "eventhomepage": "행사홈페이지",
        "eventplace": "행사장소",
        "eventstartdate": "행사시작일",
        "festivalgrade": "축제등급",
        "placeinfo": "행사장위치안내",
        "playtime": "공연시간",
        "program": "행사프로그램",
        "spendtimefestival": "관람소요시간",
        "sponsor1": "주최자정보",
        "sponsor1tel": "주최자연락처",
        "sponsor2": "주관사정보",
        "sponsor2tel": "주관사연락처",
        "subevent": "부대행사",
        "usetimefestival": "이용요금",
    },

    "25": {  # 여행코스
        "distance": "코스총거리",
        "infocentertourcourse": "문의및안내",
        "schedule": "코스일정",
        "taketime": "코스총소요시간",
        "theme": "코스테마",
    },

    "28": {  # 레포츠
        "accomcountleports": "수용인원",
        "chkbabycarriageleports": "유모차대여정보",
        "chkcreditcardleports": "신용카드가능정보",
        "chkpetleports": "애완동물동반가능정보",
        "expagerangeleports": "체험가능연령",
        "infocenterleports": "문의및안내",
        "openperiod": "개장기간",
        "parkingleports": "주차시설",
        "parkingfeeleports": "주차요금",
        "reservation": "예약안내",
        "restdateleports": "쉬는날",
        "scaleleports": "규모",
        "usefeeleports": "입장료",
        "usetimeleports": "이용시간",
    },

    "32": {  # 숙박
        "accomcountlodging": "수용가능인원",
        "checkintime": "입실시간",
        "checkouttime": "퇴실시간",
        "chkcooking": "객실내취사여부",
        "foodplace": "식음료장",
        "infocenterlodging": "문의및안내",
        "parkinglodging": "주차시설",
        "pickup": "픽업서비스",
        "roomcount": "객실수",
        "reservationlodging": "예약안내",
        "reservationurl": "예약안내홈페이지",
        "roomtype": "객실유형",
        "scalelodging": "규모",
        "subfacility": "부대시설",
        "barbecue": "바비큐장여부",
        "beauty": "뷰티시설정보",
        "beverage": "식음료장여부",
        "bicycle": "자전거대여여부",
        "campfire": "캠프파이어여부",
        "fitness": "휘트니스센터여부",
        "karaoke": "노래방여부",
        "publicbath": "공용샤워실여부",
        "publicpc": "공용PC실여부",
        "sauna": "사우나실여부",
        "seminar": "세미나실여부",
        "sports": "스포츠시설여부",
        "refundregulation": "환불규정",
    },

    "38": {  # 쇼핑
        "chkbabycarriageshopping": "유모차대여정보",
        "chkcreditcardshopping": "신용카드가능정보",
        "chkpetshopping": "애완동물동반가능정보",
        "culturecenter": "문화센터바로가기",
        "fairday": "장서는날",
        "infocentershopping": "문의및안내",
        "opendateshopping": "개장일",
        "opentime": "영업시간",
        "parkingshopping": "주차시설",
        "restdateshopping": "쉬는날",
        "restroom": "화장실설명",
        "saleitem": "판매품목",
        "saleitemcost": "판매품목별가격",
        "scaleshopping": "규모",
        "shopguide": "매장안내",
    },

    "39": {  # 음식점
        "chkcreditcardfood": "신용카드가능정보",
        "discountinfofood": "할인정보",
        "firstmenu": "대표메뉴",
        "infocenterfood": "문의및안내",
        "kidsfacility": "어린이놀이방여부",
        "opendatefood": "개업일",
        "opentimefood": "영업시간",
        "packing": "포장가능",
        "parkingfood": "주차시설",
        "reservationfood": "예약안내",
        "restdatefood": "쉬는날",
        "scalefood": "규모",
        "seat": "좌석수",
        "smoking": "금연/흡연여부",
        "treatmenu": "취급메뉴",
        "lcnsno": "인허가번호",
    },
}

        # contentTypeId에 해당하는 필드 목록
        fields = INFO_FIELDS.get(str(contenttypeid), {})

        # ---------------------------
        # ⭐ 필드 값 필터링
        # ---------------------------
        filtered_info = []
        for key, label in fields.items():
            value = raw_item.get(key)
            if value and value != "":
                filtered_info.append({
                    "label": label,
                    "value": value
                })

        print("📘 필터링된 detailInfo:", filtered_info)

        return filtered_info

    except Exception as e:
        print("❌ detailIntro2 요청 실패:", e)
        return None


























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

# DB에서 places 전체 조회
def get_all_places(db: Session):
    return db.query(Place).filter(Place.mapx.isnot(None), Place.mapy.isnot(None)).all()


def build_places_context(
    request: Request,
    db: Session,
    page: int = 1,
    sort: str = "updated",
    contenttypeid: str | None = None,
    addr: str | None = None,
    search: str | None = None,
    tag: str | None = None,
    current_user: User | None = None,
):
    per_page = 10
    offset = (page - 1) * per_page

    query = db.query(Place)

    if contenttypeid and contenttypeid.isdigit():
        query = query.filter(Place.contenttypeid == int(contenttypeid))

    if addr:
        query = query.filter(Place.addr1.startswith(addr))

    if search:
        keyword = f"%{search}%"
        query = query.filter(
            or_(
                Place.title.ilike(keyword),
                Place.overview.ilike(keyword),
            )
        )

    if tag:
        query = query.join(PlaceTag).join(Tag).filter(
            Tag.name.ilike(f"%{tag}%")
        ).distinct(Place.id)

    if sort == "updated":
        query = query.order_by(
            case((Place.firstimage != "", 1), else_=0).desc(),
            Place.updated_at.desc(),
        )
    elif sort == "created":
        query = query.order_by(
            case((Place.firstimage != "", 1), else_=0).desc(),
            Place.created_at.asc(),
        )
    else:
        query = query.order_by(
            case((Place.firstimage != "", 1), else_=0).desc(),
            Place.id.desc(),
        )

    total = query.count()
    total_pages = (total + per_page - 1) // per_page
    places = query.offset(offset).limit(per_page).all()

    pref_summary = None
    if current_user:
        places, pref_summary = sort_places_with_preferences(db, current_user.id, places)

    return {
        "places": places,
        "page": page,
        "total_pages": total_pages,
        "sort": sort,
        "contenttypeid": contenttypeid,
        "addr": addr,
        "search": search,
        "tag": tag,
        "pref_summary": pref_summary,
    }