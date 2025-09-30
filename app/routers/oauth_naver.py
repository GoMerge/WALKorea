from fastapi import APIRouter, Request, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.services.oauth_naver import (get_naver_login_url, handle_naver_callback)

router = APIRouter()


@router.get("/login")
def naver_login():
    """네이버 로그인 URL 반환"""
    return get_naver_login_url()


@router.get("/callback")
def naver_callback(request: Request, db: Session = Depends(get_db)):
    """네이버 OAuth2 콜백 처리"""
    code = request.query_params.get("code")
    state = request.query_params.get("state", "random_state_string")

    if not code:
        raise HTTPException(status_code=400, detail="Code가 필요합니다.")

    return handle_naver_callback(code, state, db)
