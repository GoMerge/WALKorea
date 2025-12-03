from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import date
from typing import List

from app.schemas.calendar import (
    UserCalendarCreate,
    UserCalendarResponse,
    CalendarEventCreate,
    CalendarEventResponse,
    ShareRequestResponse,
    ShareRequestCreate,
    ShareRespond,
)
from app.services.calendar_service import (
    create_user_calendar,
    add_schedule_to_user_calendar,
    get_user_calendars,
    get_events_for_calendar,
    update_event_in_calendar, 
    delete_event_in_calendar, 
)
from app.services.calendar_service import (
    create_share_request_service,
    list_incoming_share_requests_service,
    respond_share_request_service,
)
from app.database import get_db
from app.utils.auth import get_current_user
from app.models.user import User
from app.models.calendar import UserCalendar, CalendarShareRequest, CalendarEvent

router = APIRouter()


@router.post("/", response_model=UserCalendarResponse)
def create_calendar(
    calendar_data: UserCalendarCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    calendar_data.user_id = current_user.id
    calendar_data.event_date = date.today()
    calendar = create_user_calendar(db, calendar_data)
    return calendar


@router.get("/", response_model=List[UserCalendarResponse])
def list_user_calendars(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    calendars = get_user_calendars(db, current_user.id)
    return calendars


@router.get("/{calendar_id}/events", response_model=List[CalendarEventResponse])
def list_events_for_calendar(
    calendar_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    cal = db.query(UserCalendar).filter_by(id=calendar_id, user_id=current_user.id).first()
    if not cal:
        raise HTTPException(status_code=404, detail="캘린더가 존재하지 않습니다.")
    events = get_events_for_calendar(db, calendar_id)
    return events


@router.post("/{calendar_id}/events", response_model=CalendarEventResponse)
def create_event_for_calendar(
    calendar_id: int,
    event_data: CalendarEventCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    event = add_schedule_to_user_calendar(
        db=db,
        calendar_id=calendar_id,
        title=event_data.title,
        start_datetime=event_data.start_datetime,
        end_datetime=event_data.end_datetime,
        description=event_data.description,
        location=event_data.location,
        remind_minutes=event_data.remind_minutes,
    )
    return event

@router.put("/events/{event_id}", response_model=CalendarEventResponse)
def update_event(
    event_id: int,
    event_data: CalendarEventCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # 내가 소유한 이벤트인지 확인 (공유로 받은 일정도 수정 허용이면 calendar.user_id 검사만)
    event = (
        db.query(CalendarEvent)
        .join(UserCalendar, CalendarEvent.calendar_id == UserCalendar.id)
        .filter(
            CalendarEvent.id == event_id,
            UserCalendar.user_id == current_user.id,
        )
        .first()
    )
    if not event:
        raise HTTPException(status_code=404, detail="해당 일정이 존재하지 않습니다.")

    updated = update_event_in_calendar(
        db=db,
        event_id=event_id,
        title=event_data.title,
        start_datetime=event_data.start_datetime,
        end_datetime=event_data.end_datetime,
        description=event_data.description,
        location=event_data.location,
        remind_minutes=event_data.remind_minutes,
    )
    return updated


# 일정 삭제
@router.delete("/events/{event_id}", status_code=204)
def delete_event(
    event_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    event = (
        db.query(CalendarEvent)
        .join(UserCalendar, CalendarEvent.calendar_id == UserCalendar.id)
        .filter(
            CalendarEvent.id == event_id,
            UserCalendar.user_id == current_user.id,
        )
        .first()
    )
    if not event:
        raise HTTPException(status_code=404, detail="해당 일정이 존재하지 않습니다.")

    delete_event_in_calendar(db, event_id)
    return

# ===== 일정 공유 요청 관련 =====

@router.post("/share/request", response_model=ShareRequestResponse)
def create_share_request(
    data: ShareRequestCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    req = create_share_request_service(
        db=db,
        current_user_id=current_user.id,
        event_id=data.event_id,
        target_user_id=data.target_user_id,
    )
    return req


@router.get("/share/incoming", response_model=List[ShareRequestResponse])
def list_incoming_share_requests(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    q = (
        db.query(CalendarShareRequest)
        .filter_by(to_user_id=current_user.id, status="pending")
        .all()
    )
    return q


@router.post("/share/{request_id}/respond")
def respond_share_request(
    request_id: int,
    body: ShareRespond,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    respond_share_request_service(
        db=db,
        current_user_id=current_user.id,
        request_id=request_id,
        accept=body.accept,
    )
    return {"detail": "처리되었습니다."}
