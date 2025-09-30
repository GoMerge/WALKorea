from fastapi import APIRouter, Depends, HTTPException, Form, Query
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
from app.models.user import User
from app.schemas.auth import UserCreate, Token, RefreshTokenRequest
from app.schemas.user import SignupResponse
from app.database import get_db
from app.services.auth import signup_user, login_user, logout_service, set_nickname_service, refresh_access_token
from app.services.email import email_service  

router = APIRouter()
blacklisted_tokens = set()

# 인증 코드 발송
@router.post("/send-email-code")
def send_email_code(email: str = Query(...)):
    code = email_service.send_code(email)
    return {"message": "인증 코드가 발송되었습니다."}

@router.post("/verify-email-code")
def verify_email_code(email: str = Query(...), code: str = Query(...)):
    """인증 코드 검증"""
    email_service.verify_code(email, code)
    return {"message": "인증이 완료되었습니다."}

# 2. 회원가입 (이메일 코드 검증 포함)
@router.post("/signup", response_model=SignupResponse)
def signup_route(user_in: UserCreate, code: str, db: Session = Depends(get_db)):
    user = signup_user(user_in, code, db)
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

# 닉네임 입력 페이지
@router.get("/set-nickname", response_class=HTMLResponse)
def get_nickname_page(user_id: int, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="유저를 찾을 수 없습니다.")
    if user.nickname:
        return f"<h3>이미 닉네임이 설정되어 있습니다: {user.nickname}</h3>"

    return f"""
    <html>
        <body>
            <h3>닉네임 설정</h3>
            <form action="/auth/set-nickname" method="post">
                <input type="hidden" name="user_id" value="{user_id}">
                <input type="text" name="nickname" placeholder="닉네임 입력">
                <input type="text" name="access_token" placeholder="JWT 입력">
                <button type="submit">저장</button>
            </form>
        </body>
    </html>
    """

# 닉네임 저장
@router.post("/set-nickname")
def set_nickname(
    user_id: int = Form(...),
    nickname: str = Form(...),
    access_token: str = Form(...),
    db: Session = Depends(get_db)
):
    return set_nickname_service(user_id, nickname, access_token, db)