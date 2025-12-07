import json
from fastapi import WebSocket, HTTPException
from starlette.websockets import WebSocketState
from sqlalchemy.orm import Session
from app.models.follow import Follow
from app.models.user import User
from app.models.notification import Notification
from app.database import SessionLocal

active_connections: dict[int, WebSocket] = {}

def _create_notification(user_id: int, type_: str, message: str, data: dict | None = None):
    db = SessionLocal()
    try:
        notif = Notification(
            user_id=user_id,
            type=type_,
            message=message,
            data=None if data is None else json.dumps(data),
        )
        db.add(notif)
        db.commit()
        db.refresh(notif)
        return notif
    finally:
        db.close()

def _send_ws(user_id: int, payload: dict):
    ws = active_connections.get(user_id)
    if ws and ws.application_state == WebSocketState.CONNECTED:
        import asyncio, json
        asyncio.create_task(ws.send_text(json.dumps(payload)))

def follow_user(db: Session, follower_id: int, following_id: int) -> Follow:
    if follower_id == following_id:
        raise HTTPException(status_code=400, detail="본인은 팔로우할 수 없습니다.")

    exists = db.query(Follow).filter_by(
        follower_id=follower_id, following_id=following_id
    ).first()
    if exists:
        raise HTTPException(status_code=400, detail="이미 팔로우 중입니다.")

    follow = Follow(follower_id=follower_id, following_id=following_id)
    db.add(follow)
    db.commit()
    db.refresh(follow)

    # 닉네임 가져오기
    from_user = db.query(User).get(follower_id)
    nickname = from_user.nickname if from_user else "알 수 없음"

    msg = f"{nickname} 님이 나를 팔로우했습니다."
    print("### CREATE NOTIFICATION", following_id, "follow", msg)

    notif = _create_notification(
        user_id=following_id,
        type_="follow",
        message=msg,
        data={"from_user_id": follower_id},
    )

    _send_ws(
        following_id,
        {
            "event": "followed",
            "notification_id": notif.id,
            "message": msg,
            "from_user_id": follower_id,
        },
    )
    return follow

def notify_calendar_shared(to_user_id: int, from_user_nickname: str, calendar_title: str, date_str: str, location: str | None):
    msg = f"{from_user_nickname} 님이 '{calendar_title}' 일정을 공유했습니다."
    notif = _create_notification(
        user_id=to_user_id,
        type_="calendar_share",
        message=msg,
        data={
            "from_user_nickname": from_user_nickname,
            "title": calendar_title,
            "date": date_str,
            "location": location,
        },
    )
    _send_ws(
        to_user_id,
        {
            "event": "calendar_share",
            "notification_id": notif.id,
            "message": msg,
            "from_user_nickname": from_user_nickname,
            "title": calendar_title,
            "date": date_str,
            "location": location,
        },
    )
