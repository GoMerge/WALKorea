# app/routers/hello.py
from fastapi import APIRouter

router = APIRouter(prefix="/hello", tags=["Hello"])

@router.get("/")
def say_hello():
    return {"message": "Hello, WALKorea!"}
