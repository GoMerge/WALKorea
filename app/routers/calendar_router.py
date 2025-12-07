from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import date, datetime,timedelta
from typing import List
import calendar as calmod

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
    _ensure_date,
)
from app.database import get_db
from app.utils.auth import get_current_user
from app.models.user import User
from app.models.region import Region
from app.models.places import Festival, Place
from app.services.websocket_manager import notify_calendar_shared
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

@router.post("/share/request")
def share_calendar_event(
    body: ShareRequestCreate, 
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    # 1) 공유 대상 이벤트 조회
    ev = db.query(CalendarEvent).filter(
        CalendarEvent.id == body.event_id
    ).first()
    if not ev:
        raise HTTPException(status_code=404, detail="일정을 찾을 수 없습니다.")

    # 2) 공유 요청 레코드 저장
    req = CalendarShareRequest(
        from_user_id=current_user.id,
        to_user_id=body.target_user_id,
        event_id=body.event_id,
        status="pending",
    )
    db.add(req)
    db.commit()
    db.refresh(req)

    # 3) 알림 생성 + WebSocket 전송
    date_str = (ev.start_datetime or ev.start_date).isoformat()
    notify_calendar_shared(
        to_user_id=body.target_user_id,
        from_user_nickname=current_user.nickname,
        calendar_title=ev.title, 
        date_str=date_str,
        location=ev.location,
    )

    return {"ok": True}

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

@router.get("/share/incoming")
def list_incoming_shares(db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    rows = (
        db.query(CalendarShareRequest, CalendarEvent, User)
        .join(CalendarEvent, CalendarShareRequest.event_id == CalendarEvent.id)
        .join(User, CalendarShareRequest.from_user_id == User.id)
        .filter(CalendarShareRequest.to_user_id == current_user.id,
                CalendarShareRequest.status == "pending")
        .all()
    )
    result = []
    for req, ev, from_user in rows:
        result.append(
            {
                "id": req.id,
                "from_user_id": req.from_user_id,
                "from_user_nickname": from_user.nickname,
                "event_id": ev.id,
                "title": ev.title,
                "date": (ev.start_datetime or ev.start_date).isoformat(),
                "location": ev.location,
            }
        )
    return result

@router.get("/festivals")
def list_festivals_for_month(
    year: int,
    month: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    base_addr = getattr(current_user, "region_name", None)
    if not base_addr:
        return []

    user_city = " ".join(base_addr.split()[:2])  # 예: "인천광역시 계양구"

    first_day = date(year, month, 1)
    last_day = date(year, month, calmod.monthrange(year, month)[1])

    rows = (
        db.query(Festival, Place)
        .join(Place, Festival.place_id == Place.id)
        .filter(
            Place.addr1.contains(user_city),
            Festival.start_date <= last_day,
            Festival.end_date >= first_day,
        )
        .all()
    )

    results = []
    for fest, place in rows:
        start = max(fest.start_date, first_day)
        end = min(fest.end_date, last_day)

        d = start
        while d <= end:
            results.append(
                {
                    "id": fest.id,
                    "title": fest.title,
                    "date": d.isoformat(),
                    "location": place.addr1,
                    "detail_url": f"/places/detail/{place.id}",
                }
            )
            d = d.replace(day=d.day + 1)
    return results

@router.post("/places/{place_id}/add")
def add_place_to_calendar(
    place_id: int,
    date_str: str, 
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    # 1) 유저 캘린더 찾기
    cal = (
        db.query(UserCalendar)
        .filter(UserCalendar.user_id == current_user.id)
        .first()
    )
    if not cal:
        raise HTTPException(status_code=404, detail="캘린더가 없습니다.")

    # 2) 관광지 정보
    place = db.query(Place).filter(Place.id == place_id).first()
    if not place:
        raise HTTPException(status_code=404, detail="관광지를 찾을 수 없습니다.")

    # 3) 날짜를 datetime으로 만들기 (09:00~10:00 기본)
    d = datetime.strptime(date_str, "%Y-%m-%d")
    start = d.replace(hour=9, minute=0, second=0, microsecond=0)
    end   = start + timedelta(hours=1)

    ev = CalendarEvent(
        calendar_id=cal.id,
        title=place.title,          # 관광지 제목
        start_datetime=start,
        end_datetime=end,
        location=place.addr1,       # 관광지 주소
        description="관광지에서 추가한 일정",
    )
    db.add(ev)
    db.commit()
    db.refresh(ev)

    return {"ok": True, "event_id": ev.id}

@router.post("/places/{place_id}/events", response_model=CalendarEventResponse)
def create_event_from_place(
    place_id: int,
    visit_date: date,                     # 쿼리 파라미터로 YYYY-MM-DD
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    # 1) 내 캘린더 찾기
    cal = (
        db.query(UserCalendar)
        .filter(UserCalendar.user_id == current_user.id)
        .first()
    )
    if not cal:
        raise HTTPException(status_code=404, detail="캘린더가 없습니다.")

    # 2) 관광지 정보
    place = db.query(Place).filter(Place.id == place_id).first()
    if not place:
        raise HTTPException(status_code=404, detail="관광지를 찾을 수 없습니다.")

    # 3) 방문 시간은 기본 09:00~10:00
    start_dt = datetime.combine(visit_date, datetime.min.time()).replace(hour=9, minute=0)
    end_dt   = start_dt + timedelta(hours=1)

    ev = CalendarEvent(
        calendar_id=cal.id,
        title=place.title,          # 관광지 제목
        start_datetime=start_dt,
        end_datetime=end_dt,
        location=place.addr1,       # 관광지 주소
        description="관광지 상세에서 추가한 일정",
        from_place=True, 
    )
    db.add(ev)
    db.commit()
    db.refresh(ev)

    return ev