from sqlalchemy.orm import Session
from app.models.region import Region

def get_sidos(db: Session):
    return db.query(Region).filter(Region.level == 1).all()

def get_guguns_by_sido(db: Session, sido_id: int):
    return db.query(Region).filter(Region.level == 2, Region.parent_id == sido_id).all()

def get_dongs_by_gugun(db: Session, gugun_id: int):
    return db.query(Region).filter(Region.level == 3, Region.parent_id == gugun_id).all()
