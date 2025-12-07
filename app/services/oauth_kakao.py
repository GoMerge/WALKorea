import os
import requests
from sqlalchemy.orm import Session
from fastapi import HTTPException
from fastapi.responses import RedirectResponse
from urllib.parse import urlencode

from app.models.user import User
from app.utils.auth import create_access_token, create_refresh_token, hash_refresh_token

KAKAO_CLIENT_ID = os.getenv("KAKAO_CLIENT_ID")
KAKAO_CLIENT_SECRET = os.getenv("KAKAO_CLIENT_SECRET")
KAKAO_REDIRECT_URI = "http://127.0.0.1:8000/auth/oauth/kakao/callback"

REDIRECT_PROFILE = "http://127.0.0.1:8000/set-profile"
REDIRECT_MAIN = "http://127.0.0.1:8000/"


def get_kakao_login_url() -> dict:
    """카카오 로그인 URL 생성"""
    return {
        "login_url": (
            "https://kauth.kakao.com/oauth/authorize"
            f"?client_id={KAKAO_CLIENT_ID}"
            f"&redirect_uri={KAKAO_REDIRECT_URI}"
            "&response_type=code"
        )
    }


def handle_kakao_callback(code: str, db: Session) -> RedirectResponse:
    """카카오 OAuth2 콜백 처리"""

    # 1. 카카오 토큰 발급
    token_response = requests.post(
        "https://kauth.kakao.com/oauth/token",
        data={
            "grant_type": "authorization_code",
            "client_id": KAKAO_CLIENT_ID,
            "client_secret": KAKAO_CLIENT_SECRET,
            "redirect_uri": KAKAO_REDIRECT_URI,
            "code": code,
        },
    )
    token_response.raise_for_status()
    access_token = token_response.json().get("access_token")

    if not access_token:
        raise HTTPException(status_code=400, detail="Kakao Access Token 발급 실패")

    # 2. 카카오 사용자 정보 가져오기
    user_info = requests.get(
        "https://kapi.kakao.com/v2/user/me",
        headers={"Authorization": f"Bearer {access_token}"},
    ).json()

    kakao_account = user_info.get("kakao_account", {})
    profile = kakao_account.get("profile", {})

    email, provider_id = (
        kakao_account.get("email") or f"{user_info.get('id')}@kakao.com",
        str(user_info.get("id")),
    )

    # 3. DB 조회 or 신규 생성
    user = db.query(User).filter(User.email == email).first()
    if not user:
        user = User(
            email=email,
            name=profile.get("nickname") or "무명 사용자",
            provider="kakao",
            provider_id=provider_id,
            is_active=True,
            role="user",
        )
    else:
        # 기존 회원이면 provider 정보만 업데이트해서 연동
        user.provider = "kakao"
        user.provider_id = provider_id

    db.add(user)
    db.commit()
    db.refresh(user)

    # 4. JWT 발급 + refresh 저장 (항상 user_id 넣기)
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
