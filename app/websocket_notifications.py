from fastapi import FastAPI, WebSocket, WebSocketDisconnect
import redis.asyncio as redis
import asyncio
from datetime import datetime, timedelta

app = FastAPI()

redis_client = redis.Redis(host='127.0.0.1', port=6379, decode_responses=True)
pubsub = redis_client.pubsub()

class ConnectionManager:
    def __init__(self):
        self.active_connections = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            await connection.send_text(message)

manager = ConnectionManager()

async def redis_listener():
    await pubsub.subscribe('notifications')
    async for message in pubsub.listen():
        if message['type'] == 'message':
            await manager.broadcast(message['data'])

async def check_schedules_and_notify():
    # 일정 데이터 로드: DB 또는 별도 저장소 연동 필요
    schedule_list = [
        {"user_id": 1, "event": "Meeting", "start_time": datetime(2025, 9, 30, 10, 0, 0)},
        {"user_id": 2, "event": "Appointment", "start_time": datetime(2025, 9, 29, 22, 0, 0)}
    ]
    
    now = datetime.now()
    for schedule in schedule_list:
        time_diff = schedule['start_time'] - now
        # 24시간 +-1분 오차 범위 체크
        if timedelta(hours=23, minutes=59) <= time_diff <= timedelta(hours=24, minutes=1):
            message = f"User {schedule['user_id']}님의 일정 '{schedule['event']}'이 24시간 남았습니다."
            await redis_client.publish('notifications', message)

async def scheduler():
    while True:
        await check_schedules_and_notify()
        await asyncio.sleep(60 * 60)  # 1시간마다 체크

@app.on_event("startup")
async def startup_event():
    asyncio.create_task(redis_listener())
    asyncio.create_task(scheduler())

@app.websocket("/ws/notify")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            await redis_client.publish('notifications', data)
    except WebSocketDisconnect:
        manager.disconnect(websocket)
