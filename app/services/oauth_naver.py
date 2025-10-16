import os
import requests
from sqlalchemy.orm import Session
from fastapi import HTTPException

from app.models.user import User
from app.utils.auth import (create_access_token, create_refresh_token, hash_refresh_token)

NAVER_CLIENT_ID = os.getenv("NAVER_CLIENT_ID")
NAVER_CLIENT_SECRET = os.getenv("NAVER_CLIENT_SECRET")
NAVER_REDIRECT_URI = "http://127.0.0.1:8000/auth/oauth/naver/callback"


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


def handle_naver_callback(code: str, state: str, db: Session) -> dict:
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
            phonenum=None
        )
        db.add(user)
        db.commit()
        db.refresh(user)

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
