from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException, status, Depends
from app.database import get_db
from app.models.user import User
from app.utils.auth import hash_password, send_verification_code, verify_code, verify_password
from app.schemas.user import UserUpdate
from app.services.email import email_service

reset_tokens: dict = {}

def get_profile_service(current_user: User) -> User:
    return current_user

def update_profile_service(user_in: UserUpdate, db: Session, current_user: User):
    user_id = current_user.id
    
    # 현재 유저 조회
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다.")
    
    # 닉네임 중복 체크
    if user_in.nickname:
        existing_nickname = db.query(User).filter(
            User.nickname == user_in.nickname,
            User.id != user_id  # 자기 자신 제외
        ).first()
        if existing_nickname:
            raise HTTPException(status_code=400, detail="이미 사용 중인 닉네임입니다.")
        user.nickname = user_in.nickname

    # 나머지 필드 업데이트
    if user_in.phonenum:
        user.phonenum = user_in.phonenum
    if user_in.gender:
        user.gender = user_in.gender

    db.commit()
    db.refresh(user)
    
    return user

def change_password_service(request, db: Session, current_user: User):
    if not verify_password(request.current_password, current_user.pw_hash):
        raise HTTPException(status_code=401, detail="현재 비밀번호가 틀렸습니다.")
    current_user.pw_hash = hash_password(request.new_password)
    db.commit()
    return {"msg": "비밀번호가 변경되었습니다."}

def request_password_reset(userid: str, email: str, db: Session):
    user = db.query(User).filter(User.userid == userid, User.email == email).first()
    if not user:
        raise HTTPException(status_code=400, detail="아이디와 이메일이 일치하지 않습니다.")
    
    # 이메일 인증 코드 생성 + 발송
    code = email_service.send_code(email)
    return code

def confirm_password_reset(userid: str, email: str, verification_code: str, new_password: str, db: Session):
    user = db.query(User).filter(User.userid == userid, User.email == email).first()
    if not user:
        raise HTTPException(status_code=400, detail="아이디와 이메일이 일치하지 않습니다.")

    # 이메일 인증 코드 검증
    email_service.verify_code(email, verification_code)

    # 비밀번호 변경
    user.pw_hash = hash_password(new_password)
    db.commit()

    return {"msg": "비밀번호가 성공적으로 변경되었습니다."}

def delete_user_service(db: Session, current_user: User):
    current_user.deleted_at = datetime.utcnow()
    current_user.is_active = False
    db.commit()
    # send_account_deletion_email(current_user.email, current_user.userid)  # 기존 이메일 발송 유지
    return {"msg": "회원 탈퇴가 완료되었습니다."}
