import os
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import User
import jwt
from jwt.exceptions import PyJWTError  # 올바른 경로로 임포트

SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = "HS256"

# 토큰 발급 URL은 실제 발급 경로로 맞춰주세요
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token")

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> User:
    print("Access token received:", token)
    if SECRET_KEY is None:
        raise RuntimeError("SECRET_KEY 환경변수가 설정되어 있지 않습니다.")
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("sub")  # JWT payload 내 사용자 식별자 키 확인
    except PyJWTError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials"
        )

    user = db.query(User).filter(User.userid == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    return user
