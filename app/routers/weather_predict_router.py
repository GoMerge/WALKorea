from fastapi import APIRouter, Query
from app.services.weather_prediction_service import predict_temperature

router = APIRouter()

@router.get("/predict-temperature")
async def predict_temperature_endpoint(
    date: str = Query(..., description="예측 날짜 YYYY-MM-DD"),
    temperature: float = Query(..., description="현재 기온"),
    precipitation: float = Query(..., description="현재 강수량")
):
    try:
        predicted = predict_temperature(date, temperature, precipitation)
    except Exception:
        predicted = None
    return {"predicted_temperature": predicted}

