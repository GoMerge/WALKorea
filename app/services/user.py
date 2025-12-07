from datetime import datetime
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from app.models.user import User
from app.models.calendar import UserCalendar
from app.models.user_profile import UserProfile
from app.utils.auth import hash_password, verify_password
from app.schemas.user import UserUpdate, UserOut
from app.schemas.user import UserProfileCreate
from app.services.calendar_service import create_default_calendar_for_user
from app.services.email import email_service

def get_profile_service(current_user: User) -> UserOut:
    region_name = None
    if getattr(current_user, "region", None):
        region_name = current_user.region.full_name

    return UserOut(
        id=current_user.id,
        userid=current_user.userid,
        email=current_user.email,
        nickname=current_user.nickname,
        name=current_user.name,
        phonenum=current_user.phonenum,
        birthday=current_user.birthday,
        gender=current_user.gender,
        deleted_at=current_user.deleted_at,
        is_active=current_user.is_active,
        role=current_user.role,
        provider=current_user.provider,
        provider_id=current_user.provider_id,
        region_id=current_user.region_id,
        region_name=region_name,
    )


def get_or_create_user_calendar(db: Session, user_id: int) -> UserCalendar:
    """마이페이지 진입 시 사용: 해당 유저 캘린더가 없으면 하나 생성"""
    cal = db.query(UserCalendar).filter_by(user_id=user_id).first()
    if cal:
        return cal
    return create_default_calendar_for_user(db, user_id)

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

    if user_in.region_id is not None:
        user.region_id = user_in.region_id    
    
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

def update_user_region(db: Session, user_id: int, region_id: int):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="사용자를 찾을 수 없습니다.")
    
    user.region_id = region_id
    db.commit()
    db.refresh(user)
    return user

def create_user_profile_service(db: Session, user_id: int, profile_in: UserProfileCreate):
    profile = db.query(UserProfile).filter_by(user_id=user_id).first()
    if profile:
        profile.preferences = profile_in.preference.dict()
    else:
        profile = UserProfile(
            user_id=user_id,
            preferences=profile_in.preference.dict()
        )
        db.add(profile)
    db.commit()
    db.refresh(profile)
    return profile

def get_user_profile_service(db: Session, user_id: int):
    return db.query(UserProfile).filter_by(user_id=user_id).first()

def update_user_profile_service(db: Session, user_id: int, profile_in: UserProfileCreate):
    profile = db.query(UserProfile).filter_by(user_id=user_id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="프로필 정보가 없습니다.")
    profile.preferences = profile_in.preference.dict()
    db.commit()
    db.refresh(profile)
    return profile