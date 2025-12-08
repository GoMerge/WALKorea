from pathlib import Path
from typing import Optional
from fastapi import FastAPI, Request, Depends, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.database import get_db, Base, engine
from app.routers import (
    auth, user, oauth_google, oauth_kakao, oauth_naver,
    region_router, weather_router, calendar_router, follow, places, address_router,
    calendar_weather_router, notification_router, hashtag, favorite_router, comments,
)

BASE_DIR = Path(__file__).parent.parent  # /app/app -> /app
FRONTEND_DIR = BASE_DIR / "frontend"
templates = Jinja2Templates(directory=str(FRONTEND_DIR))

app = FastAPI(title="WALKorea API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://127.0.0.1:5500",
        "https://walkorea.com",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

Base.metadata.create_all(bind=engine)

# 모든 라우터 등록 (중복 제거)
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
app.include_router(comments.router)

# 정적 파일 마운트
app.mount("/assets", StaticFiles(directory=str(FRONTEND_DIR / "assets")), name="assets")
app.mount("/static", StaticFiles(directory=str(FRONTEND_DIR / "assets")), name="static")

@app.middleware("http")
async def log_headers(request: Request, call_next):
    response = await call_next(request)
    return response

# 메인 페이지
@app.get("/", response_class=HTMLResponse)
async def main_page(request: Request, db: Session = Depends(get_db)):
    from app.services import places as places_service
    
    try:
        ctx = places_service.build_places_context(
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
    except Exception as e:
        import traceback
        print("🔥 / main_page error:", e)
        traceback.print_exc()
        raise HTTPException(status_code=500, detail="main_page failed")

# HTML 라우트들
@app.get("/login")
async def login_page():
    return FileResponse(FRONTEND_DIR / "login.html")

@app.get("/signup")
async def signup_page():
    return FileResponse(FRONTEND_DIR / "signup.html")

@app.get("/mypage_calendar")
async def mypage_calendar():
    return FileResponse(FRONTEND_DIR / "mypage_calendar.html")

@app.get("/mypage_favorites")
async def mypage_favorites():
    return FileResponse(FRONTEND_DIR / "mypage_favorites.html")

@app.get("/mypage_friends")
async def mypage_friends():
    return FileResponse(FRONTEND_DIR / "mypage_friends.html")

@app.get("/mypage_profile")
async def mypage_profile():
    return FileResponse(FRONTEND_DIR / "mypage_profile.html")

@app.get("/mypage_recommend")
async def mypage_recommend():
    return FileResponse(FRONTEND_DIR / "mypage_recommend.html")

@app.get("/resetpw")
async def resetpw_page():
    return FileResponse(FRONTEND_DIR / "resetpw.html")

@app.get("/set-profile")
async def set_profile_page(
    user_id: Optional[int] = Query(None),
    access_token: Optional[str] = Query(None),
    refresh_token: Optional[str] = Query(None),
    need_profile: int = 0,
):
    response = FileResponse(FRONTEND_DIR / "set-profile.html")
    if access_token and refresh_token:
        response.set_cookie("access_token", access_token)
        response.set_cookie("refresh_token", refresh_token)
    return response
