
from fastapi import APIRouter, Depends, Request, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.services.places import (
    save_places_to_db,
    get_place_detail,
    get_places_page
)
from app.schemas.places import PlaceResponse
from typing import List
from app.models.places import Place, PlaceDetail
from app.models.user import User
from app.models.user_profile import UserProfile
from app.models.hashtag import PlaceTag, Tag 
from fastapi.templating import Jinja2Templates
import math
from app.utils.auth import get_current_user_optional, get_current_user
from app.services.recommendation_service import (
    sort_places_with_preferences,
    get_place_scores_for_user,
    USER_TOP_RECOMMENDED,
    TOP_N,
)
from sqlalchemy import case, exists, func  
from sqlalchemy import or_, and_
from typing import Optional



router = APIRouter()
templates = Jinja2Templates(directory="frontend/templates")


#DB 저장
@router.post("/fetch")
def fetch_and_save_places(db: Session = Depends(get_db)):
    '''
    #TourAPI 데이터를 가져와 DB에 저장
    '''
    save_places_to_db(db)
    return {"message": "TourAPI data saved successfully"}

#목록 조회
@router.get("/", response_model=list[PlaceResponse])
def read_places(db: Session = Depends(get_db)):
    '''
    #저장된 관광지 목록 조회(JSON)
    '''
    #return get_all_places(db)
    per_page = 10000  # 모든 데이터 가져오기
    return db.query(Place).order_by(Place.id.desc()).limit(per_page).all()


#상세 조회 
#@router.get("/detail/{contentid}")
#def read_place_detail(contentid: int, db: Session = Depends(get_db)):
#    '''
#    #특정관광지 상세 조회
#    '''
#    return get_place_detail(db, contentid)





    
#템플릿 상세 조회
@router.get("/detail/{contentid}")
def read_place_detail(
    request: Request,
    contentid: int,
    db: Session = Depends(get_db),
    current_user: User | None = Depends(get_current_user_optional),
):
    
    place = db.query(Place).filter(Place.contentid == contentid).first()
    if not place:
        raise HTTPException(status_code=404, detail="Place not found")
    
    # 해시태그 가져오기
    hashtags = [pt.tag for pt in place.hashtags]  # Place → PlaceTag → Tag

    # 상세정보가 PlaceDetail에 있다면 가져오기
    detail = db.query(PlaceDetail).filter_by(place_id=contentid).first()
    
    # places_detail 라우터 예시
    nearby_places = db.query(Place).filter(
        Place.mapx.isnot(None),
        Place.mapy.isnot(None),
        Place.mapy.between(place.mapy - 0.045, place.mapy + 0.045),
        Place.mapx.between(place.mapx - 0.045, place.mapx + 0.045),
        Place.contentid != contentid  # 자기 자신 제외
    ).order_by(
        func.abs(Place.mapy - place.mapy) + func.abs(Place.mapx - place.mapx)
    ).limit(20).all()
    
    def place_to_dict(p):
        return {
            "contentid": p.contentid,
            "title": p.title,
            "addr1": p.addr1 or "",
            "mapx": float(p.mapx) if p.mapx else None,
            "mapy": float(p.mapy) if p.mapy else None,
            "contenttypeid": p.contenttypeid
        }
    
    nearby_places = [place_to_dict(p) for p in nearby_places]

    
    return templates.TemplateResponse(
        "places_detail.html",
        {
            "request": request,
            "place": place,
            "detail": detail,
            "hashtags": hashtags,
            "nearby_places": nearby_places,
            "current_user": current_user,
        },
    )
  
# 목록 필터링  
@router.get("/list")
def list_places_filtered(
    request: Request,
    page: int = 1,
    sort: str = "updated",
    contenttypeid: int = None,
    addr: str = None,
    search: str = None,
    tag: str = None,
    template: str = "places_list.html",
    db: Session = Depends(get_db),
    current_user: User | None = Depends(get_current_user_optional),
):
    print(">>> /places/list current_user =", current_user.id if current_user else None)
    per_page = 10
    offset = (page - 1) * per_page

    query = db.query(Place)

    if contenttypeid:
        query = query.filter(Place.contenttypeid == contenttypeid)

    if addr:
        query = query.filter(Place.addr1.startswith(addr))

    if search:
        keyword = f"%{search}%"
        query = query.filter(
            or_(
                Place.title.ilike(keyword),
                Place.overview.ilike(keyword)
            )
        )

    if tag:
        query = query.join(PlaceTag).join(Tag).filter(
            Tag.name.ilike(f"%{tag}%")
        ).distinct(Place.id)

    if sort == "updated":
        query = query.order_by(
            case((Place.firstimage != '', 1), else_=0).desc(),
            Place.updated_at.desc()
        )
    elif sort == "created":
        query = query.order_by(
            case((Place.firstimage != '', 1), else_=0).desc(),
            Place.created_at.asc()
        )
    else:
        query = query.order_by(
            case((Place.firstimage != '', 1), else_=0).desc(),
            Place.id.desc()
        )

    total = query.count()
    total_pages = (total + per_page - 1) // per_page
    places = query.offset(offset).limit(per_page).all()

    pref_summary = None
    if current_user:
        places, pref_summary = sort_places_with_preferences(db, current_user.id, places)

    return templates.TemplateResponse(
        template,
        {
            "request": request,
            "places": places,
            "page": page,
            "total_pages": total_pages,
            "sort": sort,
            "contenttypeid": contenttypeid,
            "addr": addr,
            "search": search,
            "tag": tag,
            "pref_summary": pref_summary,   # 템플릿에서 사용할 값
        },
    )

@router.get("/recommend")
def recommend_places(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    base_query = db.query(Place)
    places: list[Place] = base_query.limit(50).all()

    sorted_places, summary, score_map = sort_places_with_preferences(
        db, current_user.id, places
    )

    top_ids = {int(p.contentid) for p in sorted_places[:TOP_N]}
    USER_TOP_RECOMMENDED[current_user.id] = top_ids
    print("TOP IDS FOR USER", current_user.id, top_ids)

    return {
        "summary": summary,
        "items": [
            {
                "id": p.contentid,
                "title": p.title,
                "addr1": p.addr1,
                "firstimage": p.firstimage,
                "scores": score_map.get(p.contentid, {}),
            }
            for p in sorted_places
        ],
    }

@router.get("/recommend/reason/{place_id}")
def get_reason(
    place_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    scores = get_place_scores_for_user(db, current_user.id, place_id)
    if scores is None:
        return {"is_recommended": False}

    return {
        "is_recommended": True,
        "base": scores["base"],
        "topic": scores["topic"],
        "distance": scores["distance"],
        "final": scores["total"],
    }
