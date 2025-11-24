from passlib.context import CryptContext
from datetime import datetime, timedelta
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from app.utils.email import send_email_code_smtp
from app.database import get_db
from app.models.user import User
from jose import JWTError, jwt
import hmac, hashlib, random, string, os
from dotenv import load_dotenv

load_dotenv()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60
REFRESH_TOKEN_EXPIRE_DAYS = 7

# 비밀번호 해시
def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

verification_store = {}

def send_verification_code(email: str, ttl_minutes: int = 10) -> str:
    """이메일 인증 코드 생성 및 만료 시간 설정"""
    code = "".join(random.choices(string.digits, k=6))
    verification_store[email] = {
        "code": code,
        "expires_at": datetime.utcnow() + timedelta(minutes=ttl_minutes)
    }
    # TODO: 실제 메일 발송
    print(f"[DEBUG] 인증 코드({email}): {code} (expires in {ttl_minutes}m)")
    return code

def verify_code(email: str, code: str) -> bool:
    rec = verification_store.get(email)
    if not rec:
        return False
    if rec["expires_at"] < datetime.utcnow():
        verification_store.pop(email, None)
        return False
    if rec["code"] != code:
        return False
    verification_store.pop(email, None)
    return True

# --- Refresh token hash / 검증 ---
def hash_refresh_token(token: str) -> str:
    return hmac.new(SECRET_KEY.encode(), token.encode(), hashlib.sha256).hexdigest()

def verify_refresh_token(token: str, token_hash: str) -> bool:
    return hash_refresh_token(token) == token_hash

# --- JWT 생성 ---
def create_access_token(data: dict) -> str:
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode = data.copy()
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def create_refresh_token(data: dict) -> str:
    expire = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode = data.copy()
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

# --- 현재 사용자 가져오기 ---
def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        userid = payload.get("sub")
        if userid is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    user = db.query(User).filter(User.userid == userid).first()
    if user is None:
        raise credentials_exception
    
    if not user.is_active or user.deleted_at is not None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Inactive or deleted user",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user

# --- 탈퇴 유저 정리 ---
def delete_expired_users(db: Session, expire_days: int = 30):
    expire_threshold = datetime.utcnow() - timedelta(days=expire_days)
    users_to_delete = db.query(User).filter(
        User.deleted_at != None,
        User.deleted_at < expire_threshold
    ).all()

    for user in users_to_delete:
        db.delete(user)
    db.commit()

# --- 토큰으로 사용자 조회 ---
def get_current_user_from_token(token: str, db: Session):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id_or_sub = payload.get("user_id") or payload.get("sub")
        if user_id_or_sub is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

        user = None
        if str(user_id_or_sub).isdigit():
            user = db.query(User).filter(User.id == int(user_id_or_sub)).first()
        if not user:
            user = db.query(User).filter(User.userid == str(user_id_or_sub)).first()
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

        return user
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token decode error")