from sqlalchemy.orm import Session
from app.models.favorite import Favorite
from app.models.places import Place 

def toggle_favorite(db: Session, user_id: int, place_id: int) -> bool:
    fav = (
        db.query(Favorite)
        .filter(Favorite.user_id == user_id, Favorite.place_id == place_id)
        .first()
    )
    if fav:
        db.delete(fav)
        db.commit()
        return False     # 좋아요 해제
    new_fav = Favorite(user_id=user_id, place_id=place_id)
    db.add(new_fav)
    db.commit()
    return True          # 좋아요 설정

def get_my_favorites(db: Session, user_id: int):
    q = (
        db.query(Place)
        .join(Favorite, Favorite.place_id == Place.contentid)
        .filter(Favorite.user_id == user_id)
        .order_by(Favorite.created_at.desc())
        .all()
    )
    return q
