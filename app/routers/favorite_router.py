from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.utils.auth import get_current_user
from app.models.user import User
from app.models.favorite import Favorite
from app.services.favorite_service import toggle_favorite, get_my_favorites

router = APIRouter(prefix="/favorites", tags=["favorites"])

@router.post("/places/{place_id}")
def toggle_favorite_route(
    place_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    liked = toggle_favorite(db, current_user.id, place_id)
    return {"liked": liked}

@router.get("/places")
def my_favorite_places(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    places = get_my_favorites(db, current_user.id)
    return [
        {
            "id": p.contentid,  
            "title": p.title,
            "addr1": p.addr1,
            "firstimage": p.firstimage,
        }
        for p in places
    ]

@router.get("/places/ids")
def get_favorite_place_ids(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    rows = (
        db.query(Favorite.place_id)
        .filter(Favorite.user_id == current_user.id)
        .all()
    )
    return [r[0] for r in rows]