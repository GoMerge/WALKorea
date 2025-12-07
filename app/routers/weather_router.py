from fastapi import APIRouter, Query, Depends, HTTPException, Response
from app.services.weather_service import get_weather, get_daily_weather_vc
from app.services.calendar_weather_service import recommend_good_days, get_avg_weather_summary,is_good_weather
from app.utils.auth import get_current_user
from app.models.user import User
from app.models.calendar import UserCalendar
from app.models.region import Region
from app.schemas.calendar import CalendarEventWeatherRequest
from app.schemas.weather import (
    CalendarWeatherResult,
    CalendarWeatherResponse,
)
from sqlalchemy.orm import Session
from fastapi.responses import FileResponse
import io, logging
from typing import List, Optional
import matplotlib.pyplot as plt
from app.database import get_db

router = APIRouter()

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

@router.get("/current")
async def current_weather(city: str = Query(..., description="도시명 (예: Seoul)")):
    weather = await get_weather(city)
    return weather

@router.get("/profile/current")
async def current_weather_profile(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if not current_user.region_id:
        raise HTTPException(status_code=404, detail="사용자에 지정된 지역이 없습니다.")

    region = db.query(Region).filter(Region.id == current_user.region_id).first()
    if not region:
        raise HTTPException(status_code=404, detail="등록된 지역 정보를 찾을 수 없습니다.")

    # ★ 모델 필드에 맞게 수정
    base_location = f"{region.sido} {region.gungu}".strip()  # 예: "서울특별시 종로구"

    weather = await get_daily_weather_vc(base_location)   # { "daily": [...] }

    return {
        "region_name": region.full_name,   # 예: "서울특별시 종로구 사직동"
        "days": weather["daily"][:6],
    }


@router.get("/calendar/{user_id}/events_with_weather")
async def get_events_with_weather(user_id: int, db: Session = Depends(get_db)):
    calendars = db.query(UserCalendar).filter(UserCalendar.user_id == user_id).all()
    events = []
    for cal in calendars:
        address = getattr(cal, "location", None)
        if not address and getattr(cal, "place", None):
            address = cal.place.address
        if not address:
            continue
        events.append({"address": address, "date": str(cal.event_date)})
    results = await recommend_good_days(events)   # 서비스 함수가 async일 때
    return {"results": results}

@router.get("/monthly-visual")
def get_monthly_weather(region: str = None):
    plt.figure()
    plot_monthly_weather_with_stddev(region_name=region)
    buf = io.BytesIO()
    plt.savefig(buf, format="png")
    buf.seek(0)
    plt.close()
    return Response(content=buf.read(), media_type="image/png")

@router.get("/map")
def get_weather_map(season: str = None):
    out_file = "weather_map.html"
    plot_weather_on_map(csv_path="data/avgWeather_with_fullname.csv", season=season, file_out=out_file)
    return FileResponse(out_file, media_type="text/html")

@router.post("/calendar/weather/recommend", response_model=CalendarWeatherResponse)
async def recommend_calendar_weather(
    items: List[CalendarEventWeatherRequest],
    db: Session = Depends(get_db),
):
    results: list[CalendarWeatherResult] = []

    for it in items:
        summary = await get_avg_weather_summary(it.address, it.date)

        avg_temp = None
        precip = None
        is_good: Optional[bool] = None

        if summary:
            avg_temp = summary.get("기온(℃)")
            precip   = summary.get("강수량(mm)")

            if avg_temp is not None and precip is not None:
                is_good = (0 <= avg_temp <= 25) and (precip < 5)

        results.append(
            CalendarWeatherResult(
                date=it.date,
                address=it.address,
                is_good=is_good,
                avg_temp=avg_temp,
                precip_mm=precip,
            )
        )

    return CalendarWeatherResponse(results=results)