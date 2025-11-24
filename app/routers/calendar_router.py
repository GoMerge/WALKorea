from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.schemas.calendar import UserCalendarCreate, UserCalendarResponse, CalendarShareCreate, CalendarShareResponse
from app.services.calendar_service import create_user_calendar, share_calendar_with_follower, get_user_calendars, get_shared_calendars_for_user
from app.database import get_db
from app.utils.auth import get_current_user
from app.models.user import User

router = APIRouter()

@router.post("/", response_model=UserCalendarResponse)
def create_calendar(
    calendar_data: UserCalendarCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    calendar_data.user_id = current_user.id
    calendar = create_user_calendar(db, calendar_data)
    return calendar

@router.post("/share/", response_model=CalendarShareResponse)
def share_calendar(
    share_data: CalendarShareCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # 공유 대상 follower_id가 본인의 팔로워인지 별도 검증 권장
    share = share_calendar_with_follower(db, share_data.calendar_id, share_data.follower_id)
    return share

@router.get("/", response_model=List[UserCalendarResponse])
def list_user_calendars(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    calendars = get_user_calendars(db, current_user.id)
    return calendars

@router.get("/shared", response_model=List[CalendarShareResponse])
def list_shared_calendars(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    shared = get_shared_calendars_for_user(db, current_user.id)
    return shared
