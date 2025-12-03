from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas.user import UserOut, UserUpdate, ChangePasswordRequest, PasswordResetRequest, PasswordResetConfirm, UserRegionUpdate, UserProfileCreate
from app.models.user import User
from app.utils.auth import get_current_user
from app.services.user import get_profile_service, change_password_service, update_profile_service, confirm_password_reset, delete_user_service
from app.services.email import EmailService
from app.services.user import request_password_reset as service_request_password_reset 
from app.services.user import create_user_profile_service

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

@router.put("/me/region")
def update_region(
    region_data: UserRegionUpdate,                
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    region_id = region_data.region_id             # 변수명도 일치해야 IDE 인식 명확
    user = db.query(User).filter(User.id == current_user.id).first()
    if not user:
        raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다.")
    user.region_id = region_id
    db.commit()
    db.refresh(user)
    return {"message": "지역이 정상적으로 설정되었습니다."}

@router.post("/user/profile/preferences")
async def create_preferences(
    profile_in: UserProfileCreate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    profile = create_user_profile_service(db, current_user.id, profile_in)
    return {"profile": profile}