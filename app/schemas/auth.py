from pydantic import BaseModel, EmailStr, constr, validator
from datetime import date
from typing import Optional
import re

class UserCreate(BaseModel):
    userid: str
    email: EmailStr
    phonenum: str
    password: str
    name: Optional[str] = None
    birthday: date   
    gender: Optional[str] = None
    nickname: Optional[str] = None

    @validator('password')
    def password_complexity(cls, v):
        if len(v) < 8:
            raise ValueError('비밀번호는 최소 8자 이상이어야 합니다.')
        if not re.search(r'[A-Z]', v):
            raise ValueError('대문자 1개 이상 필요')
        if not re.search(r'[a-z]', v):
            raise ValueError('소문자 1개 이상 필요')
        if not re.search(r'\d', v):
            raise ValueError('숫자 1개 이상 필요')
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', v):
            raise ValueError('특수문자 1개 이상 필요')
        return v

class UserLogin(BaseModel):
    userid: str
    password: str

class LogoutRequest(BaseModel):
    refresh_token: str

class Token(BaseModel):
    access_token: str
    token_type: str

class RefreshTokenRequest(BaseModel):
    refresh_token: str