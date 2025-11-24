from app.services.weather_service import get_avg_weather_summary
from app.services.weather_prediction_service import predict_temperature

def get_weather_info_for_schedule(address: str, date_str: str):
    avg_weather = get_avg_weather_summary(address, date_str)
    temperature = avg_weather["기온(℃)"] if avg_weather else None
    precipitation = avg_weather["강수량(mm)"] if avg_weather else None

    predicted_temp = predict_temperature(date_str, temperature, precipitation) if avg_weather else None

    return {
        "avg_weather": avg_weather,
        "predicted_temperature": predicted_temp,
    }

