from fastapi import FastAPI, Request, Depends, Query
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from app.database import get_db
from app.database import SessionLocal, Base, engine 
from app.routers import places
from app.routers import (
    auth, user, oauth_google, oauth_kakao, oauth_naver,
    region_router, weather_router, calendar_router, follow, places, address_router,
    calendar_weather_router, notification_router, hashtag, favorite_router, comments,
)
from pathlib import Path 
from typing import Optional

BASE_DIR = Path(__file__).parent.parent  # app/main.py → 프로젝트 루트
templates = Jinja2Templates(directory="frontend/templates")

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



Base.metadata.create_all(bind=engine)
app.include_router(places.router, prefix="/places", tags=["places"])

app.include_router(hashtag.router)

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
app.include_router(favorite_router.router)
app.include_router(comments.router)

app.mount("/assets", StaticFiles(directory=str(BASE_DIR / "frontend" / "assets")), name="assets")

app.mount("/static", StaticFiles(directory="frontend/assets"), name="static")

@app.get("/", response_class=HTMLResponse)
async def main_page(request: Request, db: Session = Depends(get_db)):
    ctx = places.build_places_context(
        request=request,
        db=db,
        page=1,
        sort="updated",
        contenttypeid=None,
        addr=None,
        search=None,
        tag=None,
        current_user=None, 
    )
    return templates.TemplateResponse("places_list.html", {"request": request, **ctx})

@app.get("/login")
async def login_page():
    return FileResponse(BASE_DIR / "frontend" / "login.html")

@app.get("/signup")
async def signup_page():
    return FileResponse(BASE_DIR / "frontend" / "signup.html")

@app.get("/mypage_calendar")
async def mypage_calendar():
    return FileResponse(BASE_DIR / "frontend" / "mypage_calendar.html")

@app.get("/mypage_favorites")
async def mypage_calendar():
    return FileResponse(BASE_DIR / "frontend" / "mypage_favorites.html")

@app.get("/mypage_friends")
async def mypage_calendar():
    return FileResponse(BASE_DIR / "frontend" / "mypage_friends.html")

@app.get("/mypage_profile")
async def mypage_calendar():
    return FileResponse(BASE_DIR / "frontend" / "mypage_profile.html")

@app.get("/mypage_recommend")
async def mypage_calendar():
    return FileResponse(BASE_DIR / "frontend" / "mypage_recommend.html")

@app.get("/resetpw")
async def mypage_calendar():
    return FileResponse(BASE_DIR / "frontend" / "resetpw.html")

@app.get("/set-profile")
async def set_profile_page(
    user_id: Optional[int] = Query(None),
    access_token: Optional[str] = Query(None),
    refresh_token: Optional[str] = Query(None),
    need_profile: int = 0,
):
    response = FileResponse(BASE_DIR / "frontend" / "set-profile.html")
    if access_token and refresh_token:
        response.set_cookie("access_token", access_token)
        response.set_cookie("refresh_token", refresh_token)
    return response
