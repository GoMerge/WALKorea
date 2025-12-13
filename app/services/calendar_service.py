from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List
from fastapi import HTTPException, status
from app.models.calendar import UserCalendar, CalendarPlace, CalendarEvent, CalendarShareRequest
from app.models.places import Place
from app.models.user import User
from app.schemas.calendar import UserCalendarCreate
from datetime import date, datetime
from app.services.follow_service import is_mutual_follow

def create_default_calendar_for_user(db: Session, user_id: int) -> UserCalendar:
    """회원가입 직후 호출해서 기본 캘린더 한 개 만들어 주는 용도"""
    calendar = UserCalendar(
        user_id=user_id,
        place_id=None,
        event_date=None,   # NOT NULL이면 date.today() 등으로 바꿔야 함
        start_time=None,
        end_time=None,
        memo="기본 캘린더",
    )
    db.add(calendar)
    db.commit()
    db.refresh(calendar)
    return calendar

### 캘린더 생성/조회/삭제
def create_user_calendar(db: Session, calendar_data: UserCalendarCreate, user_id: int) -> UserCalendar:
    calendar = UserCalendar(
        user_id=user_id,
        place_id=calendar_data.place_id,
        event_date=calendar_data.event_date or date.today(),
        start_time=None,
        end_time=None,
        memo=calendar_data.memo or "내 여행 캘린더",
    )
    db.add(calendar)
    db.commit()
    db.refresh(calendar)
    return calendar

def get_user_calendars(db: Session, user_id: int):
    return db.query(UserCalendar).filter_by(user_id=user_id).all()

def delete_user_calendar(db: Session, calendar_id: int):
    cal = db.query(UserCalendar).filter_by(id=calendar_id).first()
    if not cal:
        raise HTTPException(status_code=404, detail="해당 캘린더가 존재하지 않습니다.")
    db.delete(cal)
    db.commit()
    return True


### 개인일정(캘린더에 일정 추가/수정/삭제)
def add_schedule_to_user_calendar(
    db: Session,
    calendar_id: int,
    title: str,
    start_datetime: datetime,
    end_datetime: datetime,
    description: str | None = None,
    location: str | None = None,
    remind_minutes: int | None = None,
):
    cal = db.query(UserCalendar).filter_by(id=calendar_id).first()
    if not cal:
        raise HTTPException(404, "캘린더가 존재하지 않습니다.")

    event = CalendarEvent(
        calendar_id=calendar_id,
        title=title,
        start_datetime=start_datetime,
        end_datetime=end_datetime,
        description=description,
        location=location,
        remind_minutes=remind_minutes,
    )
    db.add(event)
    db.commit()
    db.refresh(event)
    return event

def update_event_in_calendar(
    db: Session,
    event_id: int,
    title: str | None = None,
    start_datetime: datetime | None = None,
    end_datetime: datetime | None = None,
    description: str | None = None,
    location: str | None = None,
    remind_minutes: int | None = None,
):
    event = db.query(CalendarEvent).filter_by(id=event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="해당 일정이 존재하지 않습니다.")
    if title is not None:
        event.title = title
    if start_datetime is not None:
        event.start_datetime = start_datetime
    if end_datetime is not None:
        event.end_datetime = end_datetime
    if description is not None:
        event.description = description
    if location is not None:
        event.location = location
    if remind_minutes is not None:
        event.remind_minutes = remind_minutes
    db.commit()
    db.refresh(event)
    return event

def delete_event_in_calendar(db: Session, event_id: int):
    event = db.query(CalendarEvent).filter_by(id=event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="일정이 존재하지 않습니다.")
    db.delete(event)
    db.commit()
    return True

def get_events_for_calendar(db: Session, calendar_id: int) -> List[CalendarEvent]:
    return db.query(CalendarEvent).filter_by(calendar_id=calendar_id).all()

### 관광지(Place) 일정에 추가/조회
def add_place_to_calendar(db: Session, calendar_id: int, place_id: int, visit_date: datetime):
    place = db.query(Place).filter_by(id=place_id).first()
    if not place:
        raise HTTPException(status_code=404, detail="해당 관광지가 존재하지 않습니다.")
    cal_place = CalendarPlace(
        calendar_id=calendar_id,
        place_id=place_id,
        visit_date=visit_date
    )
    db.add(cal_place)
    db.commit()
    db.refresh(cal_place)
    return cal_place

def get_places_for_calendar(db: Session, calendar_id: int):
    return db.query(CalendarPlace).filter_by(calendar_id=calendar_id).all()

### 내 위치 기반 행사/축제 자동알림 및 일정등록
def match_events_to_user_location(db: Session, user_id: int):
    user = db.query(User).filter_by(id=user_id).first()
    if not user or not user.home_address:
        raise HTTPException(status_code=400, detail="사용자 주소/위치 정보가 필요합니다.")
    user_calendar = db.query(UserCalendar).filter_by(user_id=user_id).first()
    if not user_calendar:
        raise HTTPException(status_code=404, detail="캘린더가 존재하지 않습니다.")
    address = user.home_address  # ex) '서울특별시 강서구'
    # 행사(이벤트)는 DB의 CalendarEvent, 외부 API 동기화 시 별도 테이블에서도 fetch 가능
    events = db.query(CalendarEvent).all()
    matched_events = []
    for event in events:
        # location이 행정구 포함 등 간단 매칭, 또는 위치 좌표 기반 거리 계산 적용 가능
        if address and address in (event.location or ''):
            # 이미 추가되어 있지 않은 경우만 추가
            exists = db.query(CalendarEvent).filter_by(title=event.title, start_date=event.start_date, calendar_id=user_calendar.id).first()
            if not exists:
                new_event = CalendarEvent(
                    calendar_id=user_calendar.id,
                    title=event.title,
                    start_date=event.start_date,
                    end_date=event.end_date,
                    memo="(알림) 내 주변 행사/축제"
                )
                db.add(new_event)
                matched_events.append(new_event)
    db.commit()
    return matched_events

def create_share_request_service(
    db: Session,
    current_user_id: int,
    event_id: int,
    target_user_id: int,
) -> CalendarShareRequest:
    # 1) 맞팔 확인
    if not is_mutual_follow(db, current_user_id, target_user_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="서로 팔로우가 되어 있지 않습니다.",
        )

    # 2) 내가 소유한 이벤트인지 확인
    event = (
        db.query(CalendarEvent)
        .join(UserCalendar, CalendarEvent.calendar_id == UserCalendar.id)
        .filter(
            CalendarEvent.id == event_id,
            UserCalendar.user_id == current_user_id,
        )
        .first()
    )
    if not event:
        raise HTTPException(status_code=404, detail="일정을 찾을 수 없습니다.")

    # 3) 요청 생성
    req = CalendarShareRequest(
        from_user_id=current_user_id,
        to_user_id=target_user_id,
        event_id=event_id,
        status="pending",
    )
    db.add(req)
    db.commit()
    db.refresh(req)
    return req


def list_incoming_share_requests_service(
    db: Session,
    current_user_id: int,
) -> list[CalendarShareRequest]:
    return (
        db.query(CalendarShareRequest)
        .filter_by(to_user_id=current_user_id, status="pending")
        .all()
    )


def respond_share_request_service(
    db: Session,
    current_user_id: int,
    request_id: int,
    accept: bool,
):
    req = (
        db.query(CalendarShareRequest)
        .filter_by(id=request_id, to_user_id=current_user_id, status="pending")
        .first()
    )
    if not req:
        raise HTTPException(status_code=404, detail="공유 요청을 찾을 수 없습니다.")

    if accept:
        # 원본 이벤트
        event = db.query(CalendarEvent).filter_by(id=req.event_id).first()
        if not event:
            raise HTTPException(status_code=404, detail="원본 일정을 찾을 수 없습니다.")

        # 수신자 캘린더 하나 가져오기
        cal = (
            db.query(UserCalendar)
            .filter_by(user_id=current_user_id)
            .order_by(UserCalendar.id.asc())
            .first()
        )
        if not cal:
            raise HTTPException(status_code=400, detail="내 캘린더가 없습니다.")

        # 🔥 동일 일정 존재 여부 체크 (여기 추가)
        dup_event = (
            db.query(CalendarEvent)
            .filter(
                CalendarEvent.calendar_id == cal.id,
                CalendarEvent.title == event.title,
                CalendarEvent.location == event.location,
                CalendarEvent.start_datetime == event.start_datetime,
                CalendarEvent.end_datetime == event.end_datetime,
                CalendarEvent.description == event.description,
                CalendarEvent.remind_minutes == event.remind_minutes,
            )
            .first()
        )

        if dup_event:
            # 이미 같은 일정이 있으면 새로 안 만들고 상태만 accepted로
            req.status = "accepted"
            req.responded_at = func.now()
            db.commit()
            return

        # 🔥 중복 없을 때만 새 이벤트 생성 (기존 shared_event 코드)
        shared_event = CalendarEvent(
            calendar_id=cal.id,
            title=event.title,
            start_datetime=event.start_datetime,
            end_datetime=event.end_datetime,
            location=event.location,
            description=event.description,
            remind_minutes=event.remind_minutes,
            is_shared=1,
            shared_from_user_id=req.from_user_id,
            shared_from_event_id=req.event_id,
        )
        db.add(shared_event)
        req.status = "accepted"
    else:
        req.status = "rejected"

    req.responded_at = func.now()
    db.commit()

def _ensure_date(value) -> date:
    if isinstance(value, date):
        return value
    if isinstance(value, str):
        # "20251003" 형식
        return datetime.strptime(value, "%Y%m%d").date()
    raise ValueError("invalid date")