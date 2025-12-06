from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path

# from app.services.schedule_notify_job import start_calendar_alarm_scheduler
from app.database import SessionLocal, Base, engine
from app.routers import (
    auth, user, oauth_google, oauth_kakao, oauth_naver,
    region_router, weather_router, calendar_router, follow, places, address_router,
    calendar_weather_router, notification_router, hashtag, favorite_router,
)

BASE_DIR = Path(__file__).parent.parent  # 프로젝트 루트
FRONTEND_DIR = BASE_DIR / "frontend"

app = FastAPI()

# Jinja 템플릿: frontend 디렉터리에서 바로 main.html 사용
templates = Jinja2Templates(directory=str(FRONTEND_DIR))

@app.get("/", response_class=HTMLResponse)
async def read_main(request: Request):
    return templates.TemplateResponse("main.html", {"request": request})

# 정적 파일 (assets 등)
app.mount("/assets", StaticFiles(directory=str(FRONTEND_DIR / "assets")), name="assets")

# CORS, DB, 라우터들 그대로
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://127.0.0.1:5500",
        "https://walkorea.com",
        "http://walkorea.inhatc.com",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

Base.metadata.create_all(bind=engine)
# start_calendar_alarm_scheduler(SessionLocal)

app.include_router(places.router, prefix="/places", tags=["places"])
app.include_router(hashtag.router)
app.include_router(auth.router, prefix="/auth", tags=["Auth"])
app.include_router(oauth_google.router, prefix="/auth/oauth/google", tags=["Auth OAuth"])
app.include_router(oauth_kakao.router, prefix="/auth/oauth/kakao", tags=["Auth OAuth"])
app.include_router(oauth_naver.router, prefix="/auth/oauth/naver", tags=["Auth OAuth"])
app.include_router(user.router, prefix="/user", tags=["User"])
app.include_router(region_router.router, prefix="/regions", tags=["regions"])
app.include_router(weather_router.router, prefix="/weather", tags=["Weather"])
app.include_router(calendar_router.router, prefix="/calendar", tags=["Calendar"])
app.include_router(follow.router, prefix="/follow", tags=["Follow"])
app.include_router(calendar_weather_router.router, tags=["CalendarWeather"])
app.include_router(address_router.router)
app.include_router(notification_router.router)
app.include_router(favorite_router.router)
