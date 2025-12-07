import os
import requests
from sqlalchemy.orm import Session
from fastapi import HTTPException
from fastapi.responses import RedirectResponse
from urllib.parse import urlencode

from app.models.user import User
from app.utils.auth import (
    create_access_token,
    create_refresh_token,
    hash_refresh_token,
)

GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
REDIRECT_URI = "http://127.0.0.1:8000/auth/oauth/google/callback"

REDIRECT_PROFILE = "http://127.0.0.1:8000/set-profile"
REDIRECT_MAIN = "http://127.0.0.1:8000/"


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


def handle_google_callback(code: str, db: Session) -> RedirectResponse:
    """구글 OAuth2 콜백 처리"""

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
            is_active=True,
        )
    else:
        # 이미 기존 회원이면 provider 정보만 업데이트해서 연동
        user.provider = "google"
        user.provider_id = provider_id

    db.add(user)
    db.commit()
    db.refresh(user)


    # 4. JWT 발급 + refresh 저장
    access_jwt = create_access_token({"user_id": str(user.id)})
    refresh_jwt = create_refresh_token({"user_id": str(user.id)})
    user.refresh_token = hash_refresh_token(refresh_jwt)
    db.commit()

    # 5. 프로필(닉네임/생일/성별) 비어있으면 set-profile.html로
    need_profile = not user.nickname or not user.birthday or not user.gender

    if need_profile:
        params = urlencode({
            "user_id": user.id,
            "access_token": access_jwt,
            "refresh_token": refresh_jwt,
            "need_profile": 1,
        })
        return RedirectResponse(f"{REDIRECT_PROFILE}?{params}")

    # 전부 있으면 메인으로
    params_ok = urlencode({
        "access_token": access_jwt,
        "refresh_token": refresh_jwt,
    })
    return RedirectResponse(f"{REDIRECT_MAIN}?{params_ok}")
