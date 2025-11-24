from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from datetime import timedelta
from app.models.user import User
from app.schemas.auth import UserCreate
from app.schemas.user import UserOut
from app.utils.auth import (hash_refresh_token, hash_password, verify_password, create_access_token,
    create_refresh_token, get_current_user_from_token)
from app.services.email import email_service

blacklisted_tokens = set()

# 회원가입
def signup_user(user_in: UserCreate, code: str, db: Session):
    email_service.verify_code(user_in.email, code)
    phonenum_value = getattr(user_in, "phonenum", None)  # 일반 가입

    existing_user = db.query(User).filter(
        (User.userid == user_in.userid) | (User.email == user_in.email)
    ).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="이미 존재하는 사용자입니다.")

    user = User(
        userid=user_in.userid,
        email=user_in.email,
        pw_hash=hash_password(user_in.password),
        name=user_in.name,
        phonenum=phonenum_value,
        birthday=user_in.birthday,
        gender=user_in.gender,
        nickname=user_in.nickname,
        is_active=True,
        role="user",  # role 기본값 추가
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    return UserOut(
        id=user.id,
        userid=user.userid,
        email=user.email,
        name=user.name,
        phonenum=user.phonenum,
        birthday=user.birthday,
        gender=user.gender,
        role=user.role,
        nickname=user.nickname,
        provider=user.provider,
        provider_id=user.provider_id
    )

# 로그인
def login_user(userid: str, password: str, db: Session):
    user = db.query(User).filter(User.userid == userid).first()
    if not user or not verify_password(password, user.pw_hash):
        raise HTTPException(status_code=401, detail="아이디 또는 비밀번호가 잘못되었습니다.")
    if not user.is_active or user.deleted_at is not None:
        raise HTTPException(status_code=401, detail="비활성 혹은 탈퇴된 사용자입니다.")

    access_token = create_access_token({"sub": user.userid, "role": user.role})
    refresh_token = create_refresh_token({"sub": user.userid})

    user.refresh_token_hash = hash_refresh_token(refresh_token)
    db.commit()
    db.refresh(user)

    return {"access_token": access_token, "refresh_token": refresh_token, "token_type": "bearer"}

# 로그아웃
def logout_service(refresh_token: str, db: Session):
    hashed_token = hash_refresh_token(refresh_token)
    user = db.query(User).filter(User.refresh_token_hash == hashed_token).first()
    if user:
        user.refresh_token_hash = None
        db.commit()
    return {"msg": "로그아웃 완료"}


# 액세스 토큰 재발급
def refresh_access_token(refresh_token: str, db: Session):
    # DB에서 refresh_token 검증
    hashed_token = hash_refresh_token(refresh_token)
    user = db.query(User).filter(User.refresh_token_hash == hashed_token).first()
    if not user:
        raise HTTPException(status_code=401, detail="유효하지 않은 리프레시 토큰입니다.")
    access_token = create_access_token({"sub": user.userid, "role": user.role})
    return {"access_token": access_token, "token_type": "bearer"}

# 닉네임 설정
def set_nickname_service(user_id: int, nickname: str, access_token: str, db: Session):
    current_user = get_current_user_from_token(access_token, db)

    if current_user.id != user_id:
        raise HTTPException(status_code=403, detail="잘못된 접근입니다.")

    if db.query(User).filter(User.nickname == nickname).first():
        raise HTTPException(status_code=400, detail="이미 사용 중인 닉네임입니다.")

    current_user.nickname = nickname
    db.commit()
    db.refresh(current_user)

    return {"msg": "닉네임 설정 완료", "nickname": current_user.nickname}