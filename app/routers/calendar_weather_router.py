from fastapi import APIRouter, Body, Depends
from typing import List, Dict, Any
from sqlalchemy.orm import Session
from app.database import get_db
from app.utils.auth import get_current_user
from app.models.user import User
from app.services.calendar_weather_service import recommend_good_days
from app.schemas.calendar import CalendarEventWeatherRequest

router = APIRouter()

@router.post("/calendar/weather/recommend")
async def calendar_weather_recommend(
    events: List[CalendarEventWeatherRequest],   # { address, date } 리스트 그대로 받기
    current_user = Depends(get_current_user),  # 필요하면 인증만
):
    calendar_events: List[Dict[str, Any]] = [
        {"address": ev.address, "date": ev.date}
        for ev in events
    ]
    results = await recommend_good_days(calendar_events)
    return {"results": results}