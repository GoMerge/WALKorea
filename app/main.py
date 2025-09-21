from fastapi import FastAPI
from app.routers import auth, user
from app.scheduler import start_scheduler

app = FastAPI()

# 라우터 등록
app.include_router(auth.router, prefix="/auth")
app.include_router(user.router, prefix="/user")

# 스케줄러 시작
start_scheduler()
