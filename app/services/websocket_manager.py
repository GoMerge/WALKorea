# app/services/notification_service.py

import json
import asyncio
from datetime import datetime
from typing import Any, Dict, Optional

from fastapi import WebSocket, HTTPException
from starlette.websockets import WebSocketState
from sqlalchemy.orm import Session

from app.models.follow import Follow
from app.models.user import User
from app.models.notification import Notification

# 로그인한 유저의 WebSocket 연결을 user_id 기준으로 보관
active_connections: dict[int, WebSocket] = {}


def create_notification(
    db: Session,
    user_id: int,
    type_: str,
    message: str,
    data: Optional[dict[str, Any]] = None,
) -> Notification:
    notif = Notification(
        user_id=user_id,
        type=type_,
        message=message,
        data=json.dumps(data) if isinstance(data, dict) else data,
        is_read=False,
        created_at=datetime.utcnow(),
    )
    db.add(notif)
    db.commit()
    db.refresh(notif)
    return notif


def _send_ws(user_id: int, payload: dict):
    ws = active_connections.get(user_id)
    if ws and ws.application_state == WebSocketState.CONNECTED:
        asyncio.create_task(ws.send_text(json.dumps(payload)))


def follow_user(db: Session, follower_id: int, following_id: int) -> Follow:
    if follower_id == following_id:
        raise HTTPException(status_code=400, detail="본인은 팔로우할 수 없습니다.")

    exists = (
        db.query(Follow)
        .filter_by(follower_id=follower_id, following_id=following_id)
        .first()
    )
    if exists:
        raise HTTPException(status_code=400, detail="이미 팔로우 중입니다.")

    follow = Follow(follower_id=follower_id, following_id=following_id)
    db.add(follow)
    db.commit()
    db.refresh(follow)

    # 닉네임 가져오기
    from_user = db.get(User, follower_id)
    nickname = from_user.nickname if from_user else "알 수 없음"

    msg = f"{nickname} 님이 나를 팔로우했습니다."

    notif = create_notification(
        db=db,
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


def notify_calendar_shared(
    db: Session,
    to_user_id: int,
    from_user_nickname: str,
    calendar_title: str,
    date_str: str,
    location: Optional[str],
):
    msg = f"{from_user_nickname} 님이 '{calendar_title}' 일정을 공유했습니다."
    notif = create_notification(
        db=db,
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
