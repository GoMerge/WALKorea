from celery import Celery
from app.utils.push import send_push_notification
from app.database import SessionLocal
from app.models.calendar import UserCalendar
from datetime import datetime

celery = Celery(
    "worker",
    broker="redis://localhost:6379/0",
    backend="redis://localhost:6379/0"
)

@celery.task
def send_calendar_notification(event_id: int):
    db = SessionLocal()
    try:
        event = db.query(UserCalendar).filter(UserCalendar.id == event_id).first()
        if not event:
            return
        user = event.user  # ORM 관계로 사용자 정보 접근
        title = f"일정 알림: {event.event_type or '일정'}"
        message = f"{event.memo or '등록한 일정'}가 24시간 남았습니다."
        send_push_notification(user.id, title, message)
    finally:
        db.close()

def schedule_notification(event_id: int, notify_time: datetime):
    delay = (notify_time - datetime.utcnow()).total_seconds()
    if delay > 0:
        send_calendar_notification.apply_async(args=[event_id], countdown=delay)
    else:
        send_calendar_notification.delay(event_id)
