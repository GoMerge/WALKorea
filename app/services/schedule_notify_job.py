# app/services/schedule_notify_job.py
import asyncio
from datetime import datetime, timedelta
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from sqlalchemy.orm import Session
from app.services.websocket_manager import active_connections
from app.models.calendar import UserCalendar 
from fastapi import WebSocket
from starlette.websockets import WebSocketState

def notify_calendar_event(to_user_id: int, event_title: str, event_time: str):
    ws: WebSocket = active_connections.get(to_user_id)
    if ws and ws.application_state == WebSocketState.CONNECTED:
        import json
        message = {
            "event": "calendar_reminder",
            "title": event_title,
            "start_time": event_time,
            "message": f'일정 "{event_title}"(이)가 24시간 후 시작됩니다!'
        }
        asyncio.create_task(ws.send_text(json.dumps(message)))

def calendar_check_job(session_factory):
    db: Session = session_factory()
    now = datetime.now()
    right_time = now + timedelta(hours=24)
    # 24시간 뒤에 시작하는 일정 찾기 (날짜는 DB 타입에 따라 parsing 필요)
    events = db.query(UserCalendar).filter(UserCalendar.start_time.between(right_time.replace(minute=0, second=0, microsecond=0),
                                                            right_time.replace(minute=59, second=59, microsecond=999999))).all()
    for ev in events:
        notify_calendar_event(ev.user_id, ev.title, ev.start_time.strftime("%Y-%m-%d %H:%M"))
    db.close()

def start_calendar_alarm_scheduler(session_factory):
    scheduler = AsyncIOScheduler()
    scheduler.add_job(calendar_check_job, 'interval', minutes=60, args=[session_factory])
    scheduler.start()
