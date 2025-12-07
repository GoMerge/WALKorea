import os
import requests
from sqlalchemy.orm import Session
from fastapi import HTTPException
from fastapi.responses import RedirectResponse
from urllib.parse import urlencode

from app.models.user import User
from app.utils.auth import create_access_token, create_refresh_token, hash_refresh_token

NAVER_CLIENT_ID = os.getenv("NAVER_CLIENT_ID")
NAVER_CLIENT_SECRET = os.getenv("NAVER_CLIENT_SECRET")
NAVER_REDIRECT_URI = "http://127.0.0.1:8000/auth/oauth/naver/callback"

REDIRECT_PROFILE = "http://127.0.0.1:8000/set-profile"
REDIRECT_MAIN = "http://127.0.0.1:8000/"


def get_naver_login_url() -> dict:
    """네이버 로그인 URL 생성"""
    return {
        "login_url": (
            "https://nid.naver.com/oauth2.0/authorize"
            f"?client_id={NAVER_CLIENT_ID}"
            f"&redirect_uri={NAVER_REDIRECT_URI}"
            "&response_type=code"
            "&state=random_state_string"
        )
    }


def handle_naver_callback(code: str, state: str, db: Session) -> RedirectResponse:
    """네이버 OAuth2 콜백 처리"""

    # 1. 네이버 토큰 발급
    token_response = requests.post(
        "https://nid.naver.com/oauth2.0/token",
        data={
            "grant_type": "authorization_code",
            "client_id": NAVER_CLIENT_ID,
            "client_secret": NAVER_CLIENT_SECRET,
            "redirect_uri": NAVER_REDIRECT_URI,
            "code": code,
            "state": state,
        },
    )
    token_response.raise_for_status()
    access_token = token_response.json().get("access_token")

    if not access_token:
        raise HTTPException(status_code=400, detail="Naver Access Token 발급 실패")

    # 2. 네이버 사용자 정보
    user_info = requests.get(
        "https://openapi.naver.com/v1/nid/me",
        headers={"Authorization": f"Bearer {access_token}"},
    ).json().get("response", {})

    email, provider_id = (
        user_info.get("email") or f"{user_info.get('id')}@naver.com",
        str(user_info.get("id")),
    )

    # 3. DB 조회 or 신규 생성
    user = db.query(User).filter(User.email == email).first()
    if not user:
        user = User(
            email=email,
            name=user_info.get("nickname") or "무명 사용자",
            provider="naver",
            provider_id=provider_id,
            is_active=True,
            role="user",
        )
    else:
        # 기존 회원이면 provider 정보만 업데이트해서 연동
        user.provider = "naver"
        user.provider_id = provider_id

    db.add(user)
    db.commit()
    db.refresh(user)

    # 4. JWT 발급 (항상 user_id 사용) + refresh 저장
    access_jwt = create_access_token({"user_id": str(user.id)})
    refresh_jwt = create_refresh_token({"user_id": str(user.id)})
    user.refresh_token = hash_refresh_token(refresh_jwt)
    db.commit()

    # 5. 닉네임/생일/성별 비어 있으면 프로필 설정 페이지로
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
