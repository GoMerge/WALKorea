# app/routers/region_router.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.schemas.region import RegionBase
from app.services.region_service import (
    get_sidos,
    get_guguns_by_sido,
    get_dongs_by_gugun,
)

router = APIRouter()

@router.get("/sidos", response_model=List[RegionBase])
def sidos(db: Session = Depends(get_db)):
    items = get_sidos(db)
    if not items:
        raise HTTPException(404, "시·도를 찾을 수 없습니다.")
    return items

@router.get("/guguns/{sido_id}", response_model=List[RegionBase])
def guguns(sido_id: int, db: Session = Depends(get_db)):
    items = get_guguns_by_sido(db, sido_id)
    if not items:
        raise HTTPException(404, "구를 찾을 수 없습니다.")
    return items

@router.get("/dongs/{gugun_id}", response_model=List[RegionBase])
def dongs(gugun_id: int, db: Session = Depends(get_db)):
    items = get_dongs_by_gugun(db, gugun_id)
    if not items:
        raise HTTPException(404, "동을 찾을 수 없습니다.")
    return items
