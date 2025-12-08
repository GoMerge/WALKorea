from sqlalchemy.orm import Session
from fastapi import HTTPException, status, WebSocket
from app.services.websocket_manager import active_connections, create_notification
from starlette.websockets import WebSocketState
from app.models.follow import Follow  # ORM 모델
from app.models.user import User

def get_users_by_nickname_like(db: Session, nickname: str):
    pattern = f"%{nickname}%"
    users = db.query(User).filter(User.nickname.ilike(pattern)).all()
    return users  # 빈 리스트 반환 허용

def get_users_by_nickname_like_or_404(db: Session, nickname: str):
    users = get_users_by_nickname_like(db, nickname)
    if not users:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="해당하는 닉네임 사용자를 찾을 수 없습니다.")
    return users

def get_user_by_nickname(db: Session, nickname: str) -> User:
    user = db.query(User).filter(User.nickname == nickname).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="사용자를 찾을 수 없습니다.")
    return user

def follow_user(db: Session, follower_id: int, following_id: int) -> Follow:
    if follower_id == following_id:
        raise HTTPException(status_code=400, detail="본인은 팔로우할 수 없습니다.")

    exists = db.query(Follow).filter_by(
        follower_id=follower_id, following_id=following_id
    ).first()
    if exists:
        raise HTTPException(status_code=400, detail="이미 팔로우 중입니다.")

    print("FOLLOW CALL", follower_id, "->", following_id)

    # 닉네임 가져오기
    from_user = db.query(User).get(follower_id)
    nickname = from_user.nickname if from_user else "알 수 없음"

    msg = f"{nickname} 님이 나를 팔로우했습니다."

    # DB Notification 생성
    notif = create_notification(
        user_id=following_id,
        type_="follow",
        message=msg,
        data={"from_user_id": follower_id},
    )

    follow = Follow(follower_id=follower_id, following_id=following_id)
    print("### CREATE NOTIFICATION", following_id, "follow", msg)
    print("ACTIVE CONNS", active_connections.keys())
    db.add(follow)
    db.commit()
    db.refresh(follow)

    # WebSocket으로도 보내고 싶으면 여기서 notify_follow_event 호출
    notify_follow_event(to_user_id=following_id, from_user_id=follower_id)

    return follow

def notify_follow_event(to_user_id: int, from_user_id: int):
    ws: WebSocket = active_connections.get(to_user_id)
    if ws and ws.application_state == WebSocketState.CONNECTED:
        import asyncio
        import json
        message = {"event": "followed", "from_user_id": from_user_id}
        asyncio.create_task(ws.send_text(json.dumps(message)))

def unfollow_user(db: Session, follower_id: int, following_id: int):
    follow = db.query(Follow).filter_by(follower_id=follower_id, following_id=following_id).first()
    if not follow:
        raise HTTPException(status_code=404, detail="팔로우 관계가 존재하지 않습니다.")
    db.delete(follow)
    db.commit()

def get_following_list(db: Session, user_id: int):
    rows = (
        db.query(Follow, User.nickname)
        .join(User, Follow.following_id == User.id)
        .filter(Follow.follower_id == user_id)
        .all()
    )
    result = []
    for follow, nickname in rows:
        follow.following_nickname = nickname 
        result.append(follow)
    return result


def get_follower_list(db: Session, user_id: int):
    rows = (
        db.query(Follow, User.nickname)
        .join(User, Follow.follower_id == User.id)
        .filter(Follow.following_id == user_id)
        .all()
    )
    result = []
    for follow, nickname in rows:
        follow.follower_nickname = nickname
        result.append(follow)
    return result


def is_mutual_follow(db: Session, user_a: int, user_b: int) -> bool:
    a_to_b = db.query(Follow).filter_by(follower_id=user_a, following_id=user_b).first()
    b_to_a = db.query(Follow).filter_by(follower_id=user_b, following_id=user_a).first()
    return bool(a_to_b and b_to_a)