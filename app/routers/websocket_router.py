from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from app.services.websocket_manager import active_connections

router = APIRouter()

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
