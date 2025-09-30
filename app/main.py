from fastapi import FastAPI
from app.routers import auth, user, oauth_google, oauth_kakao, oauth_naver
from app.scheduler import start_scheduler

app = FastAPI()

# /auth 그룹
app.include_router(auth.router, prefix="/auth", tags=["Auth"])
# /auth/oauth
app.include_router(oauth_google.router, prefix="/auth/oauth/google", tags=["Auth OAuth"])
app.include_router(oauth_kakao.router, prefix="/auth/oauth/kakao", tags=["Auth OAuth"])
app.include_router(oauth_naver.router, prefix="/auth/oauth/naver", tags=["Auth OAuth"])

# /user 그룹
app.include_router(user.router, prefix="/user", tags=["User"])

# 스케줄러 시작
start_scheduler()