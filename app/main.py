# app/main.py
from fastapi import FastAPI
from app.routers import hello  # 라우터 임포트

app = FastAPI(
    title="WALKorea API",
    description="WALKorea 프로젝트용 FastAPI 서버",
    version="0.1.0"
)

# 라우터 등록
app.include_router(hello.router)

# 기본 root 엔드포인트
@app.get("/")
def root():
    return {"message": "Welcome to WALKorea API 🚀"}
