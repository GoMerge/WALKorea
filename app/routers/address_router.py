# app/routers/address_router.py
from typing import List
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.region import Region
from app.schemas.region import RegionSearchItem

router = APIRouter(prefix="/address", tags=["address"])

@router.get("/search", response_model=List[RegionSearchItem])
def search_region(
    q: str = Query(..., min_length=1, description="검색어(시/구/동/리 등)"),
    limit: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db),
):
    """
    Region 테이블에서 full_name / name / sido / gungu / myeon_eupdong / ri_dong
    에 대해 부분 일치 검색.
    """
    tokens = [t for t in q.strip().split() if t]
    if not tokens:
        return []

    query = db.query(Region)

    for t in tokens:
        like = f"%{t}%"
        query = query.filter(
            (Region.full_name.ilike(like)) |
            (Region.name.ilike(like)) |
            (Region.sido.ilike(like)) |
            (Region.gungu.ilike(like)) |
            (Region.myeon_eupdong.ilike(like)) |
            (Region.ri_dong.ilike(like))
        )

    rows = query.order_by(Region.level, Region.full_name).limit(limit).all()

    results: List[RegionSearchItem] = []
    for r in rows:
        # full_name 있으면 그대로, 없으면 파트 합치기
        if r.full_name:
            full = r.full_name
        else:
            parts = [r.sido, r.gungu, r.myeon_eupdong, r.ri_dong, r.name]
            full = " ".join(p for p in parts if p)

        results.append(
            RegionSearchItem(
                id=r.id,
                code=r.code,
                full_name=full,
            )
        )
    return results
