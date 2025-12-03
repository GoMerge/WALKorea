from fastapi import APIRouter, Depends, HTTPException, Form, Query
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
from app.models.user import User
from app.schemas.auth import UserCreate, Token, RefreshTokenRequest
from app.schemas.user import SignupResponse
from app.database import get_db
from app.utils.redis_client import set_cached, get_cached
from app.services.auth import signup_user, login_user, logout_service, set_profile_service, refresh_access_token
from app.services.email import email_service  

router = APIRouter()
blacklisted_tokens = set()

@router.post("/send-email-code")
def send_email_code(email: str = Form(...), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == email).first()
    if user:
        raise HTTPException(status_code=400, detail="이미 회원가입 된 이메일입니다")
    code = email_service.send_code(email)
    return {"message": "인증 코드가 발송되었습니다."}

# 인증코드 검증 성공 시
@router.post("/verify-email-code")
async def verify_email_code(email: str = Form(...), code: str = Form(...)):
    email_service.verify_code(email, code)
    await set_cached(f"email_verified:{email}", "1", expire_seconds=600)
    return {"message": "인증이 완료되었습니다."}


@router.get("/check-id")
def check_id(userid: str, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.userid == userid).first()
    if user:
        # 이미 존재
        return {"result": "dup"}
    else:
        # 사용가능
        return {"result": "ok"}

@router.get("/check-nickname")
def check_nickname(nickname: str, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.nickname == nickname).first()
    if user:
        return {"result": "dup"}
    else:
        return {"result": "ok"}

# 2. 회원가입 (이메일 코드 검증 포함)
@router.post("/signup", response_model=SignupResponse)
async def signup_route(user_in: UserCreate, db: Session = Depends(get_db)):
    is_verified = await get_cached(f"email_verified:{user_in.email}")
    if is_verified != "1":
        raise HTTPException(status_code=400, detail="이메일 인증이 되지 않았습니다.")
    user = signup_user(user_in, db)  # code 없이 호출할 것!
    return SignupResponse(msg="회원가입 완료", user=user)

# 로그인
@router.post("/login")
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    return login_user(form_data.username, form_data.password, db)

# 액세스 토큰 재발급
@router.post("/refresh", response_model=Token)
def refresh_token(request: RefreshTokenRequest, db: Session = Depends(get_db)):
    return refresh_access_token(request.refresh_token, db)

# 로그아웃
@router.post("/logout")
def logout(refresh_token: str, db: Session = Depends(get_db)):
    return logout_service(refresh_token, db)

@router.post("/set-profile")
def set_profile(
    user_id: int = Form(...),
    nickname: str = Form(...),
    access_token: str = Form(...),
    birthday: str = Form(...),
    gender: str = Form(...),
    db: Session = Depends(get_db)
):
    return set_profile_service(user_id, nickname, access_token, birthday, gender, db)

