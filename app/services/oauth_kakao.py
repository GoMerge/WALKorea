import os
import requests
from sqlalchemy.orm import Session
from fastapi import HTTPException

from app.models.user import User
from app.utils.auth import (create_access_token, create_refresh_token, hash_refresh_token)

KAKAO_CLIENT_ID = os.getenv("KAKAO_CLIENT_ID")
KAKAO_CLIENT_SECRET = os.getenv("KAKAO_CLIENT_SECRET")
KAKAO_REDIRECT_URI = "http://127.0.0.1:8000/auth/oauth/kakao/callback"


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


def handle_kakao_callback(code: str, db: Session) -> dict:
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
        )
        db.add(user)
        db.commit()
        db.refresh(user)

    # 4. JWT 발급
    access_jwt = create_access_token({"user_id": str(user.id)})
    refresh_jwt = create_refresh_token({"user_id": str(user.id)})
    user.refresh_token = hash_refresh_token(refresh_jwt)
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
