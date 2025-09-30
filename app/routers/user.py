from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas.user import UserOut, UserUpdate, ChangePasswordRequest, PasswordResetRequest, PasswordResetConfirm
from app.models.user import User
from app.utils.auth import get_current_user
from app.services.user import get_profile_service, change_password_service, update_profile_service, request_password_reset, confirm_password_reset, delete_user_service
from app.services.email import EmailService
from app.services.user import request_password_reset as service_request_password_reset

router = APIRouter()
email = EmailService()

@router.get("/profile", response_model=UserOut)
def get_profile(current_user: User = Depends(get_current_user)):
    return get_profile_service(current_user)


@router.put("/profile", response_model=UserOut)
def update_profile(
    user_in: UserUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
):
    return update_profile_service(user_in, db, current_user)


@router.post("/change-pw")
def change_password(
    request: ChangePasswordRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
):
    return change_password_service(request, db, current_user)

# 1. 비밀번호 재설정 요청
@router.post("/password-reset-request")
def password_reset_request(req: PasswordResetRequest, db: Session = Depends(get_db)):
    code = service_request_password_reset(req.userid, req.email, db)
    return {"msg": "비밀번호 초기화 코드가 발송되었습니다.", "code": code}

# 2. 비밀번호 재설정 완료
@router.post("/password-reset-confirm")
def password_reset_confirm(req: PasswordResetConfirm, db: Session = Depends(get_db)):
    return confirm_password_reset(req.userid, req.email, req.verification_code, req.new_password, db)

@router.delete("/delete")
def delete_user(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return delete_user_service(db, current_user)