from pydantic import BaseModel, EmailStr, constr, Field, validator
from typing import Optional
from datetime import date, datetime
import re

class UserBase(BaseModel):
    name: Optional[str]
    phonenum: Optional[str]
    birthday: Optional[date]
    gender: Optional[str]
    deleted_at: Optional[datetime] = None
    is_active: bool = True
    
    class Config:
        orm_mode = True

class UserCreate(BaseModel):
    userid: str
    email: EmailStr
    phonenum: str
    password: str  # 비밀번호 입력 필드
    name: str        # 이름
    birthday: date   # 생일
    gender: str      # 성별

    @validator('password')
    def password_complexity(cls, v):
        if len(v) < 8:
            raise ValueError('비밀번호는 최소 8자 이상이어야 합니다.')
        if not re.search(r'[A-Z]', v):
            raise ValueError('비밀번호에 최소 한 개의 대문자가 포함되어야 합니다.')
        if not re.search(r'[a-z]', v):
            raise ValueError('비밀번호에 최소 한 개의 소문자가 포함되어야 합니다.')
        if not re.search(r'\d', v):
            raise ValueError('비밀번호에 최소 한 개의 숫자가 포함되어야 합니다.')
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', v):
            raise ValueError('비밀번호에 최소 한 개의 특수문자가 포함되어야 합니다.')
        return v

class UserUpdate(UserBase):
    pass  # 필요한 필드 추가

class UserOut(UserBase):
    id: int
    userid: Optional[str]
    email: EmailStr
    role: str

    class Config:
        orm_mode = True
