from sqlalchemy.orm import Session
from app.models.region import Region
from app.schemas.weather import SimpleWeather
from app.utils.weather import is_good_weather, is_good_weather_from_avg
from app.utils.convert_address import convert_address_to_coordinates
from app.services.weather_service import get_avg_weather_summary, get_daily_weather_vc
# from app.services.weather_prediction_service import predict_temperature


async def resolve_region_fullname_from_address(address: str, db: Session) -> str | None:
    coords = convert_address_to_coordinates(address)
    if coords is None:
        return None
    lat, lon = coords

    region = (
        db.query(Region)
        .order_by(
            (Region.lat - lat) * (Region.lat - lat) +
            (Region.lon - lon) * (Region.lon - lon)
        )
        .first()
    )
    return region.full_name if region else None


async def get_weather_info_for_schedule(address: str, date_str: str):
    avg_weather = await get_avg_weather_summary(address, date_str)
    temperature = avg_weather["기온(℃)"] if avg_weather else None
    precipitation = avg_weather["강수량(mm)"] if avg_weather else None

    predicted_temp = (
        predict_temperature(date_str, temperature, precipitation)
        if avg_weather else None
    )

    return {
        "avg_weather": avg_weather,
        "predicted_temperature": predicted_temp,
    }


async def recommend_good_days(calendar_events):
    results = []
    for ev in calendar_events:
        date = ev["date"]
        addr = ev["address"]

        info = await get_weather_info_for_schedule(addr, date)
        avg = info["avg_weather"]

        is_good = None
        if avg:
            # 1) CSV 평년값 기반 기본 판정
            w = SimpleWeather(
                month=int(date[5:7]),
                avg_temperature=float(avg.get("기온(℃)") or 0.0),
                avg_precipitation=float(avg.get("강수량(mm)") or 0.0),
                cloud_percent=0.0,
                wind_speed=0.0,
                avg_humidity=50.0,
            )
            ok_climate = is_good_weather(w)  # ← CSV 기준만

            # 2) 예보가 있는 날짜(앞 6일 등)만 추가 컷
            fc_map = await get_daily_weather_vc(addr)
            fc = None
            for d in fc_map["daily"]:
                if d["date"] == date:
                    fc = d
                    break

            ok_actual = True
            if fc:
                tmin = fc.get("temp_min")
                tmax = fc.get("temp_max")
                icon = fc.get("icon")

                if tmin is not None and tmin < -3:
                    ok_actual = False
                if tmax is not None and tmax > 30:
                    ok_actual = False
                if icon in ("rain", "snow", "sleet"):
                    ok_actual = False

            is_good = ok_climate and ok_actual

        results.append({
            "date": date,
            "address": addr,
            "is_good": is_good,
            "weather": info,
        })

    return results



def classify_weather_quality(
    avg_temp: float | None,
    avg_precip: float | None,
    today_temp: float | None,
    today_precip: float | None,
) -> str:
    """
    avg_* : 평년(30년 평균) 값
    today_* : 예측/실제 값
    return: "good" / "normal" / "bad"
    """
    if today_temp is None or avg_temp is None:
        return "normal"  

    dt = abs(float(today_temp) - float(avg_temp))

    dp = 0.0
    if avg_precip is not None and today_precip is not None:
        dp = float(today_precip) - float(avg_precip)
    elif today_precip is not None:
        dp = float(today_precip)

    score = 0.0

    if dt <= 2:
        score += 2.0
    elif dt <= 5:
        score += 1.0
    else:
        score -= 1.0

    if dp <= 0.5:
        score += 1.0
    elif dp >= 3.0:
        score -= 1.0

    if score >= 2.0:
        return "good"
    if score <= 0.0:
        return "bad"
    return "normal"
