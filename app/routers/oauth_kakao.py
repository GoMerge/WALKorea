from fastapi import APIRouter, Request, Depends, HTTPException
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app.database import get_db
from app.services.oauth_kakao import get_kakao_login_url, handle_kakao_callback

router = APIRouter()

@router.get("/login")
def kakao_login():
    """카카오 로그인 페이지로 즉시 리다이렉트"""
    url = get_kakao_login_url()["login_url"]
    return RedirectResponse(url)

@router.get("/callback", response_class=RedirectResponse)
def kakao_callback(request: Request, db: Session = Depends(get_db)):
    """카카오 OAuth2 콜백 처리"""
    code = request.query_params.get("code")
    if not code:
        raise HTTPException(status_code=400, detail="Code가 필요합니다.")
    return handle_kakao_callback(code, db)
