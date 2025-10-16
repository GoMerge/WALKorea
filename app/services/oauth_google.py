import os, uuid
import requests
from sqlalchemy.orm import Session
from fastapi import HTTPException

from app.models.user import User
from app.utils.auth import (create_access_token,create_refresh_token,hash_refresh_token)

GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
REDIRECT_URI = "http://127.0.0.1:8000/auth/oauth/google/callback"


def get_google_login_url() -> dict:
    """구글 로그인 URL 생성"""
    return {
        "login_url": (
            "https://accounts.google.com/o/oauth2/v2/auth"
            f"?client_id={GOOGLE_CLIENT_ID}"
            f"&redirect_uri={REDIRECT_URI}"
            "&response_type=code"
            "&scope=email profile openid"
        )
    }


def handle_google_callback(code: str, db: Session) -> dict:
    """구글 OAuth2 콜백 처리"""

    print("DB 세션 연결 확인:", db.bind)

    # 1. 구글 토큰 발급
    token_response = requests.post(
        "https://oauth2.googleapis.com/token",
        data={
            "code": code,
            "client_id": GOOGLE_CLIENT_ID,
            "client_secret": GOOGLE_CLIENT_SECRET,
            "redirect_uri": REDIRECT_URI,
            "grant_type": "authorization_code",
        },
    )
    token_response.raise_for_status()
    access_token = token_response.json().get("access_token")

    if not access_token:
        raise HTTPException(status_code=400, detail="Google Access Token 발급 실패")

    # 2. 구글 사용자 정보 가져오기
    user_info = requests.get(
        "https://www.googleapis.com/oauth2/v2/userinfo",
        headers={"Authorization": f"Bearer {access_token}"},
    ).json()

    email, provider_id = (
        user_info.get("email") or f"{user_info.get('id')}@google.com",
        user_info.get("id"),
    )

    # 3. DB 조회 or 신규 생성
    user = db.query(User).filter(User.email == email).first()
    if not user:
        user = User(
            email=email,
            name=user_info.get("name") or "무명 사용자",
            provider="google",
            provider_id=provider_id,
            phonenum=str(uuid.uuid4())[:20]
        )
        try:
            db.add(user)
            db.commit()       # 여기서 예외가 발생하면 rollback 됨
            db.refresh(user)
        except Exception as e:
            db.rollback()
            print("DB INSERT ERROR:", e)
            raise HTTPException(status_code=500, detail="사용자 생성 실패")

    # 4. JWT 발급
    access_jwt = create_access_token({"user_id": str(user.id)})
    refresh_jwt = create_refresh_token({"user_id": str(user.id)})
    user.refresh_token_hash = hash_refresh_token(refresh_jwt)
    db.commit()

    # 5. 닉네임 여부 확인 후 응답
    if not user.nickname:
        return {
            "msg": "닉네임 설정이 필요합니다.",
            "redirect": f"/auth/set-nickname?user_id={user.id}",
            "access_token": access_jwt,
            "refresh_token": refresh_jwt,
        }

    return {
        "msg": "로그인 성공",
        "user": {
            "id": user.id,
            "email": user.email,
            "name": user.name,
            "nickname": user.nickname,
        },
        "access_token": access_jwt,
        "refresh_token": refresh_jwt,
    }