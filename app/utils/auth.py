from passlib.context import CryptContext
from datetime import datetime, timedelta
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import User
from jose import JWTError, jwt
from jwt import InvalidTokenError
from typing import Optional
import hmac, hashlib, random, string
import os
from dotenv import load_dotenv

load_dotenv()
SECRET_KEY = os.getenv("SECRET_KEY")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60
REFRESH_TOKEN_EXPIRE_DAYS = 7

MAX_PASSWORD_BYTES = 72  # bcrypt 한계

# 비밀번호 해시
def hash_password(password: str) -> str:
    # bcrypt 한계 초과 시 400 에러를 던지도록
    if len(password.encode("utf-8")) > MAX_PASSWORD_BYTES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="비밀번호는 최대 72자 이하로 입력해주세요.",
        )
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
    
    #  1. 빈 토큰 / 너무 짧은 토큰 체크
    if not token or len(token.strip()) < 20:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or empty token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    try:
        #  2. JWT 형식 검사 (3부분 있는지)
        if token.count('.') != 2:
            raise jwt.DecodeError("Invalid JWT format")
        
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("user_id")
        if user_id is None:
            raise credentials_exception
    except jwt.DecodeError as e:
        #  3. DecodeError 구체적으로 잡기
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid token format: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except JWTError:
        raise credentials_exception

    user = db.query(User).filter(User.id == int(user_id)).first()
    if user is None:
        raise credentials_exception

    if not user.is_active or user.deleted_at is not None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Inactive or deleted user",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user


def get_optional_token(request: Request) -> Optional[str]:
    auth = request.headers.get("Authorization")
    if not auth or not auth.lower().startswith("bearer "):
        return None
    return auth.split(" ", 1)[1]

def get_current_user_optional(
    token: Optional[str] = Depends(get_optional_token),
    db: Session = Depends(get_db),
) -> Optional[User]:
    if not token:
        return None
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("user_id")
        if user_id is None:
            return None
    except Exception:
        return None

    user = db.query(User).filter(User.id == int(user_id)).first()
    if not user or (not user.is_active or user.deleted_at is not None):
        return None
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
def get_current_user_from_token(token: str, db: Session) -> User:
    if SECRET_KEY is None:
        raise RuntimeError("SECRET_KEY 환경변수가 설정되어 있지 않습니다.")
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("user_id") 
        if user_id is None:
            raise HTTPException(status_code=401, detail="토큰에 user_id가 없습니다.")
    except InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid authentication credentials")

    user = db.query(User).filter(User.id == int(user_id)).first() 
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user
