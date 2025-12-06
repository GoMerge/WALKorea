from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent  # /app/app -> /app
FRONTEND_DIR = BASE_DIR / "frontend"

app = FastAPI(title="WALKorea API")

# frontend 디렉터리에서 main.html 사용
templates = Jinja2Templates(directory=str(FRONTEND_DIR))

@app.get("/", response_class=HTMLResponse)
async def read_main(request: Request):
    return templates.TemplateResponse("main.html", {"request": request})

# 정적 파일 (예: /assets)
app.mount("/assets", StaticFiles(directory=str(FRONTEND_DIR / "assets")), name="assets")
