from pydantic import BaseModel
from datetime import datetime

class FollowCreate(BaseModel):
    following_id: int  # 팔로우할 사용자 ID

class FollowResponse(BaseModel):
    follower_id: int
    following_id: int
    created_at: datetime
    follower_nickname: str | None = None
    following_nickname: str | None = None

    class Config:
        from_attributes  = True

class NicknameSearchResponse(BaseModel):
    user_id: int
    nickname: str