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
from fastapi.templating import Jinja2Templates
import math
from sqlalchemy import case



#router = APIRouter(prefix="/places", tags=["Places"])

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


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
def read_place_detail(request: Request, contentid: int, db: Session = Depends(get_db)):
    """
    특정 관광지 상세 조회 및 HTML 렌더링
    """
    # Place 기본 정보
    place = db.query(Place).filter(Place.contentid == contentid).first()
    if not place:
        raise HTTPException(status_code=404, detail="Place not found")
    
    # 해시태그 가져오기
    hashtags = [pt.tag for pt in place.hashtags]  # Place → PlaceTag → Tag

    # 상세정보가 PlaceDetail에 있다면 가져오기
    detail = db.query(PlaceDetail).filter_by(place_id=contentid).first()
    
    return templates.TemplateResponse(
        "places_detail.html",
        {
            "request": request,
            "place": place,
            "detail": detail,
            "hashtags": hashtags
        }
    )
  
# 목록 필터링  
@router.get("/list")
def list_places_filtered(
    request: Request,
    page: int = 1,
    sort: str = "updated",  # 'updated' 최신순, 'created' 오래된순
    contenttypeid: int = None,  # 관광타입 필터
    addr: str = None,  # addr1 앞 2글자 필터
    template: str = "places_list.html", 
    db: Session = Depends(get_db),
):
    per_page = 10  # 페이지당 항목 수 고정
    offset = (page - 1) * per_page

    query = db.query(Place)

    # contenttypeid 필터
    if contenttypeid:
        query = query.filter(Place.contenttypeid == contenttypeid)

    # addr1 앞 2글자 필터
    if addr:
        query = query.filter(Place.addr1.startswith(addr))

    # 정렬
    if sort == "updated":
        query = query.order_by(
            case((Place.firstimage != '', 1), else_=0).desc(),  # firstimage 있는 것 먼저
            Place.updated_at.desc()  # 최신순
        )
    elif sort == "created":
        query = query.order_by(
            case((Place.firstimage != '', 1), else_=0).desc(),  # firstimage 있는 것 먼저
            Place.created_at.asc()  # 오래된순
        )
    else:
        query = query.order_by(
            case((Place.firstimage != '', 1), else_=0).desc(),
            Place.id.desc()                       # 기본 정렬
        )

    total = query.count()
    total_pages = (total + per_page - 1) // per_page
    places = query.offset(offset).limit(per_page).all()

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
        },
    )