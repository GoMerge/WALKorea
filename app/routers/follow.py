from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.utils.auth import get_current_user
from app.database import get_db
from app.schemas.follow import FollowCreate, FollowResponse
from app.models.user import User
from pydantic import BaseModel
from app.services.follow_service import (
    follow_user,
    unfollow_user,
    get_following_list,
    get_follower_list,
    get_users_by_nickname_like_or_404,
)


router = APIRouter()


class NicknameSearchResponse(BaseModel):
    user_id: int
    nickname: str

    class Config:
        orm_mode = True


@router.post("/", response_model=FollowResponse)
def create_follow(
    follow_data: FollowCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    follow = follow_user(db, current_user.id, follow_data.following_id)
    return follow


@router.get("/search-by-nickname/", response_model=list[NicknameSearchResponse])
def search_users(
    nickname: str,
    db: Session = Depends(get_db),
):
    users = get_users_by_nickname_like_or_404(db, nickname)
    return [NicknameSearchResponse(user_id=u.id, nickname=u.nickname) for u in users]


@router.post("/follow-user/")
def follow_user_by_id(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    follow_user(db, current_user.id, user_id)
    return {"detail": f"{user_id} 번 사용자를 팔로우했습니다."}


@router.delete("/{following_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_follow(
    following_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    unfollow_user(db, current_user.id, following_id)


@router.get("/following", response_model=list[FollowResponse])
def list_following(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return get_following_list(db, current_user.id)


@router.get("/followers", response_model=list[FollowResponse])
def list_followers(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return get_follower_list(db, current_user.id)
