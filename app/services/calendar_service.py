from sqlalchemy.orm import Session
from fastapi import HTTPException
from app.models.calendar import UserCalendar, CalendarShare, CalendarPlace, CalendarEvent
from app.models.place import Place
from app.models.user import User  # 유저 프로필(위치 알림용) 모델
from datetime import datetime

### 캘린더 생성/조회/삭제
def create_user_calendar(db: Session, calendar_data):
    calendar = UserCalendar(**calendar_data.dict())
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

### 캘린더 공유
def share_calendar_with_follower(db: Session, calendar_id: int, follower_id: int):
    exists = db.query(CalendarShare).filter_by(calendar_id=calendar_id, follower_id=follower_id).first()
    if exists:
        raise HTTPException(status_code=400, detail="이미 공유된 일정입니다.")
    share = CalendarShare(calendar_id=calendar_id, follower_id=follower_id)
    db.add(share)
    db.commit()
    db.refresh(share)
    return share

def get_shared_calendars_for_user(db: Session, follower_id: int):
    return db.query(CalendarShare).filter_by(follower_id=follower_id).all()

### 개인일정(캘린더에 일정 추가/수정/삭제)
def add_schedule_to_user_calendar(db: Session, calendar_id: int, title: str, start_date: datetime, end_date: datetime, memo: str = None):
    event = CalendarEvent(
        calendar_id=calendar_id,
        title=title,
        start_date=start_date,
        end_date=end_date,
        memo=memo
    )
    db.add(event)
    db.commit()
    db.refresh(event)
    return event

def update_event_in_calendar(db: Session, event_id: int, title: str = None, start_date: datetime = None, end_date: datetime = None, memo: str = None):
    event = db.query(CalendarEvent).filter_by(id=event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="해당 일정이 존재하지 않습니다.")
    if title:
        event.title = title
    if start_date:
        event.start_date = start_date
    if end_date:
        event.end_date = end_date
    if memo:
        event.memo = memo
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

def get_events_for_calendar(db: Session, calendar_id: int):
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

