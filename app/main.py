from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from app.services.schedule_notify_job import start_calendar_alarm_scheduler
from app.database import SessionLocal
from app.routers import (
    auth, user, oauth_google, oauth_kakao, oauth_naver,
    region_router, weather_router, calendar_router, follow, places, address_router,
    calendar_weather_router, notification_router, 
)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://127.0.0.1:5500",       # 프론트 개발 URL
        "https://walkorea.com",        # 실서비스 도메인
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)




app.include_router(places.router, prefix="/places", tags=["places"])

start_calendar_alarm_scheduler(SessionLocal) 

@app.middleware("http")
async def log_headers(request: Request, call_next):
    response = await call_next(request)
    return response

# /auth 그룹
app.include_router(auth.router, prefix="/auth", tags=["Auth"])
app.include_router(oauth_google.router, prefix="/auth/oauth/google", tags=["Auth OAuth"])
app.include_router(oauth_kakao.router, prefix="/auth/oauth/kakao", tags=["Auth OAuth"])
app.include_router(oauth_naver.router, prefix="/auth/oauth/naver", tags=["Auth OAuth"])

# /user 그룹
app.include_router(user.router, prefix="/user", tags=["User"])

# region, weather, calendar, follow 

app.include_router(region_router.router, prefix="/regions", tags=["regions"])
app.include_router(weather_router.router, prefix="/weather", tags=["Weather"])
app.include_router(calendar_router.router, prefix="/calendar", tags=["Calendar"])
app.include_router(follow.router, prefix="/follow", tags=["Follow"])
app.include_router(calendar_weather_router.router, tags=["CalendarWeather"])

app.include_router(address_router.router)
app.include_router(notification_router.router)

app.mount("/", StaticFiles(directory="frontend/TheProperty", html=True), name="static")