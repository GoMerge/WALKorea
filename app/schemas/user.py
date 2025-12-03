from pydantic import BaseModel, EmailStr, validator, Field
from typing import Optional, List
from datetime import date, datetime
import re

class UserBase(BaseModel):
    name: Optional[str]
    phonenum: Optional[str]
    birthday: Optional[date]
    gender: Optional[str]
    nickname: Optional[str]
    deleted_at: Optional[datetime] = None
    is_active: bool = True

    class Config:
        from_attributes   = True

class UserOut(UserBase):
    id: int
    userid: Optional[str]
    email: EmailStr
    nickname: Optional[str]
    role: str
    provider: Optional[str] = None
    provider_id: Optional[str] = None
    region_id: Optional[int] = None
    region_name: Optional[str] = None

class SignupResponse(BaseModel):
    msg: str
    user: UserOut

class UserUpdate(BaseModel):
    phonenum: str
    nickname: Optional[str] = None
    gender: Optional[str] = None

# 비밀번호 변경/초기화
class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str
    @validator("new_password")
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError("비밀번호는 최소 8자 이상이어야 합니다.")
        if not re.search(r"[A-Z]", v):
            raise ValueError("비밀번호에 대문자가 최소 1개 포함되어야 합니다.")
        if not re.search(r"[a-z]", v):
            raise ValueError("비밀번호에 소문자가 최소 1개 포함되어야 합니다.")
        if not re.search(r"\d", v):
            raise ValueError("비밀번호에 숫자가 최소 1개 포함되어야 합니다.")
        if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", v):
            raise ValueError("비밀번호에 특수문자가 최소 1개 포함되어야 합니다.")
        return v

# --- Request Schemas ---
class PasswordResetRequest(BaseModel):
    userid: str
    email: str

class PasswordResetConfirm(BaseModel):
    userid: str
    email: str
    verification_code: str
    new_password: str = Field(..., min_length=8)

    @validator("new_password")
    def validate_password(cls, v):
        if not re.search(r"[A-Z]", v):
            raise ValueError("비밀번호에는 최소 1개의 대문자가 필요합니다.")
        if not re.search(r"[a-z]", v):
            raise ValueError("비밀번호에는 최소 1개의 소문자가 필요합니다.")
        if not re.search(r"\d", v):
            raise ValueError("비밀번호에는 최소 1개의 숫자가 필요합니다.")
        if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", v):
            raise ValueError("비밀번호에는 최소 1개의 특수문자가 필요합니다.")
        return v

class DeleteUserRequest(BaseModel):
    password: str

class UserRegionUpdate(BaseModel):
    region_id: int  # 필수로 지역 ID를 제공받음

class UserRegionResponse(BaseModel):
    id: int
    region_id: int

    class Config:
        from_attributes  = True

class UserPreferenceSchema(BaseModel):
    age_group: Optional[str] = Field(default="알 수 없음", description="연령대")
    gender: Optional[str] = Field(default="알 수 없음")
    travel_with: Optional[List[str]] = Field(default=["혼자", "친구", "가족", "커플", "단체", "어린이"])
    travel_style: Optional[str] = Field(default="계획형")
    activity_level: Optional[str] = Field(default="비활동적")
    area_theme: Optional[List[str]] = Field(default=["바다", "산", "도시", "자연"])
    activity_type: Optional[List[str]] = Field(default=["문화체험", "맛집", "휴식", "관광명소"])
    photo_likes: Optional[str] = Field(default="보통")
    vibe: Optional[str] = Field(default="조용한 곳")
    night_activity: Optional[str] = Field(default="낮활동")
    sns_like: Optional[bool] = Field(default=False)
    avoid_crowd: Optional[bool] = Field(default=False)

class UserProfileCreate(BaseModel):
    preference: UserPreferenceSchema