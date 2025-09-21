from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from pydantic import BaseModel, constr, EmailStr
from datetime import datetime
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas.user import UserOut, UserUpdate
from app.models.user import User
from app.utils.auth import get_current_user, verify_password, hash_password
from app.utils.email import send_reset_password_email, send_account_deletion_email
import uuid

router = APIRouter()

class ChangePasswordRequest(BaseModel):
    current_password: constr(min_length=8)
    new_password: constr(min_length=8)

class ResetPasswordRequest(BaseModel):
    email: EmailStr

class ResetPasswordConfirm(BaseModel):
    token: constr(min_length=36, max_length=36)
    new_password: constr(min_length=8)

class DeleteUserRequest(BaseModel):
    password: constr(min_length=8)

reset_tokens = {}

@router.get("/profile", response_model=UserOut)
def get_profile(current_user: User = Depends(get_current_user)):
    return current_user

@router.put("/profile", response_model=UserOut)
def update_profile(user_in: UserUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if current_user is None:
        raise HTTPException(status_code=401, detail="Unauthorized user.")
    for field, value in user_in.dict(exclude_unset=True).items():
        setattr(current_user, field, value)
    db.commit()
    db.refresh(current_user)
    return current_user

@router.post("/change-pw")
def change_password(request: ChangePasswordRequest, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    if not verify_password(request.current_password, current_user.pw_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="현재 비밀번호가 틀렸습니다.")
    current_user.pw_hash = hash_password(request.new_password)
    db.commit()
    return {"msg": "비밀번호가 변경되었습니다."}

@router.post("/reset-pw-request")
def reset_password_request(request: ResetPasswordRequest, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == request.email).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="등록된 이메일이 없습니다.")
    token = str(uuid.uuid4())
    reset_tokens[token] = user.id
    send_reset_password_email(user.email, token)
    background_tasks.add_task(send_reset_password_email, user.email, token)
    return {"msg": "비밀번호 재설정 이메일을 발송했습니다."}

@router.post("/reset-pw")
def reset_password_confirm(request: ResetPasswordConfirm, db: Session = Depends(get_db)):
    user_id = reset_tokens.get(request.token)
    if not user_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="토큰이 유효하지 않거나 만료되었습니다.")
    user = db.query(User).get(user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="사용자를 찾을 수 없습니다.")
    user.pw_hash = hash_password(request.new_password)
    db.commit()
    del reset_tokens[request.token]
    return {"msg": "비밀번호가 성공적으로 재설정되었습니다."}

@router.delete("/delete", status_code=status.HTTP_200_OK)
def delete_user(db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    current_user.deleted_at = datetime.utcnow()
    current_user.is_active = False
    db.commit()

    send_account_deletion_email(current_user.email, current_user.userid)
    return {"msg": "회원 탈퇴가 완료되었습니다."}

@router.get("/me")
def read_users_me(current_user: User = Depends(get_current_user)):
    return current_user
