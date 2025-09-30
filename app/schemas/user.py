from pydantic import BaseModel, EmailStr, validator, Field
from typing import Optional
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
        orm_mode = True

class UserOut(UserBase):
    id: int
    userid: Optional[str]
    email: EmailStr
    nickname: Optional[str]
    role: str
    provider: Optional[str] = None
    provider_id: Optional[str] = None

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