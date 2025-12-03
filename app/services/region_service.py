# app/services/region_service.py
from sqlalchemy.orm import Session
from app.models.region import Region

def get_sidos(db: Session):
    return (
        db.query(Region)
        .filter(Region.level == 1)      # level=1: 시·도
        .order_by(Region.name)
        .all()
    )

def get_guguns_by_sido(db: Session, sido_id: int):
    return (
        db.query(Region)
        .filter(Region.parent_id == sido_id, Region.level == 2)  # level=2: 시·군·구
        .order_by(Region.name)
        .all()
    )

def get_dongs_by_gugun(db: Session, gugun_id: int):
    return (
        db.query(Region)
        .filter(Region.parent_id == gugun_id, Region.level == 3)  # level=3: 동·읍·면
        .order_by(Region.name)
        .all()
    )
