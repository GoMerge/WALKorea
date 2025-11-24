from pydantic import BaseModel
from datetime import date, time
from typing import Optional

class UserCalendarBase(BaseModel):
    user_id: int
    place_id: Optional[int]
    event_date: date
    start_time: Optional[time] = None
    end_time: Optional[time] = None
    memo: Optional[str] = None

class UserCalendarCreate(UserCalendarBase):
    pass

class UserCalendarResponse(UserCalendarBase):
    id: int

    class Config:
        from_attributes = True

class CalendarShareCreate(BaseModel):
    calendar_id: int
    follower_id: int

class CalendarShareResponse(BaseModel):
    id: int
    calendar_id: int
    follower_id: int
    shared_at: str

    class Config:
        from_attributes  = True

class CalendarEventWeatherRequest(BaseModel):
    address: str
    date: str  # "YYYY-MM-DD"