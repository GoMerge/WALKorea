from fastapi import APIRouter, Depends, Request, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.services.places import (
    save_places_to_db,
    get_all_places,
    get_place_detail
)
from app.schemas.places import PlaceResponse
from typing import List
from app.models.places import Place
from fastapi.templating import Jinja2Templates
import math


#router = APIRouter(prefix="/places", tags=["Places"])
router = APIRouter()

templates = Jinja2Templates(directory="app/templates")  # 경로 프로젝트 구조에 맞게 조정


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
    return get_all_places(db)


#상세 조회 
@router.get("/{contentid}")
def read_place_detail(contentid: int, db: Session = Depends(get_db)):
    '''
    #특정관광지 상세 조회
    '''
    return get_place_detail(db, contentid)

#목록 조회
@router.get("/places")
def list_places(request: Request, page: int = 1, db: Session = Depends(get_db)):
    per_page = 10
    if page < 1:
        page = 1
    total = db.query(Place).count()
    total_pages = math.ceil(total / per_page)
    offset = (page - 1) * per_page
    places = db.query(Place).order_by(Place.id.desc()).offset(offset).limit(per_page).all()
    return templates.TemplateResponse(
        "places_list.html",
        {
            "request": request,
            "places": places,
            "page": page,
            "total_pages": total_pages
        }
    )