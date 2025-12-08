from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session
from app.database import get_db
from app.utils.auth import get_current_user
from app.models.notification import Notification
from app.services.websocket_manager import active_connections

router = APIRouter()

@router.get("/")
def list_notifications(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    items = (
        db.query(Notification)
        .filter(Notification.user_id == current_user.id)
        .order_by(Notification.created_at.desc())
        .all()
    )
    return [
        {
            "id": n.id,
            "type": n.type,
            "message": n.message,
            "is_read": n.is_read,
            "created_at": n.created_at.isoformat(),
            "data": n.data,
        }
        for n in items
    ]

@router.websocket("/ws/notify/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: int):
    await websocket.accept()
    active_connections[user_id] = websocket
    try:
        while True:
            _ = await websocket.receive_text()
    except WebSocketDisconnect:
        if user_id in active_connections:
            del active_connections[user_id]

@router.delete("/{notif_id}")
def delete_notification(
    notif_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    q = db.query(Notification).filter(
        Notification.id == notif_id,
        Notification.user_id == current_user.id,
    )
    if not q.first():
        return
    q.delete()
    db.commit()
