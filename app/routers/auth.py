from fastapi import APIRouter, Depends, HTTPException, status, Header
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel
from datetime import timedelta
from sqlalchemy.orm import Session
from app.schemas.user import UserCreate, UserOut
from app.models.user import User
from app.database import get_db
from app.utils.auth import hash_password, verify_password, create_access_token, verify_refresh_token

router = APIRouter()

blacklisted_tokens = set()

@router.post("/signup", response_model=UserOut)
def signup(user_in: UserCreate, db: Session = Depends(get_db)):
    existing_user = db.query(User).filter((User.userid == user_in.userid) | (User.email == user_in.email)).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="UserID 또는 이메일이 이미 존재합니다.")
    existing_phone = db.query(User).filter(User.phonenum == user_in.phonenum).first()
    if existing_phone:
        raise HTTPException(status_code=400, detail="이미 등록된 핸드폰 번호입니다.")

    user = User(
        userid=user_in.userid,
        email=user_in.email,
        is_active=True,
        deleted_at=None,
        pw_hash=hash_password(user_in.password),
        name=user_in.name,
        phonenum=user_in.phonenum,
        birthday=user_in.birthday,
        gender=user_in.gender,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

@router.post("/login")
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.userid == form_data.username).first()
    
    if not user or not user.pw_hash or not verify_password(form_data.password, user.pw_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="아이디 또는 비밀번호가 잘못되었습니다.")
    
    if not user.is_active or user.deleted_at is not None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="비활성 혹은 탈퇴된 사용자입니다.")
    
    access_token = create_access_token(data={"sub": user.userid, "role": user.role})
    return {"access_token": access_token, "token_type": "bearer", "msg": "login successful"}

@router.post("/logout")
def logout(refresh_token: str = Header(...)):
    if not verify_refresh_token(refresh_token):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token.")
    blacklisted_tokens.add(refresh_token)
    return {"msg": "로그아웃 처리되었습니다."}

class TokenRefreshRequest(BaseModel):
    refresh_token: str

@router.post("/token")
def token_refresh(request: TokenRefreshRequest):
    if not verify_refresh_token(request.refresh_token):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token.")
    user_data = {"sub": "userid_example", "role": "user"}  # 실제 토큰 데이터 디코딩 후 사용
    access_token = create_access_token(data=user_data, expires_delta=timedelta(minutes=60))
    return {"access_token": access_token, "token_type": "bearer"}
