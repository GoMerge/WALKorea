from pydantic import BaseModel, Field
from datetime import date, time, datetime
from typing import Optional

class UserCalendarBase(BaseModel):
    user_id: int
    place_id: Optional[int]
    event_date: date
    start_time: Optional[time] = None
    end_time: Optional[time] = None
    memo: Optional[str] = None

class UserCalendarCreate(BaseModel):
    place_id: Optional[int] = None
    event_date: date
    memo: Optional[str] = "내 여행 캘린더"  

class UserCalendarResponse(UserCalendarBase):
    id: int

    class Config:
        from_attributes = True

class CalendarEventBase(BaseModel):
    title: str
    start_datetime: datetime = Field(alias="start_date")
    end_datetime: datetime = Field(alias="end_date")
    location: Optional[str] = None
    description: Optional[str] = Field(default=None, alias="memo")
    remind_minutes: Optional[int] = None

    class Config:
        populate_by_name = True
        from_attributes = True

class CalendarEventCreate(CalendarEventBase):
    pass

class CalendarEventResponse(CalendarEventBase):
    id: int
    is_shared: int
    shared_from_user_id: Optional[int] = None
    shared_from_event_id: Optional[int] = None
    from_place: bool = False

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
        from_attributes = True


class CalendarEventWeatherRequest(BaseModel):
    address: str
    date: str  # "YYYY-MM-DD"

class ShareRequestCreate(BaseModel):
    event_id: int
    target_user_id: int

class ShareRequestResponse(BaseModel):
    id: int
    from_user_id: int
    to_user_id: int
    event_id: int
    status: str
    from_user_nickname: str | None = None

    class Config:
        from_attributes = True

class ShareRespond(BaseModel):
    accept: bool