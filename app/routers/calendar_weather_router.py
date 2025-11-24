from fastapi import APIRouter, Body
from typing import List
from app.services.calendar_weather_service import recommend_good_days
from app.schemas.calendar import CalendarEventWeatherRequest

router = APIRouter()

@router.post("/calendar/weather/recommend")
async def recommend_calendar_good_days(
    calendar_events: List[CalendarEventWeatherRequest] = Body(...)
):
    result = await recommend_good_days([e.dict() for e in calendar_events])
    return {"results": result}
