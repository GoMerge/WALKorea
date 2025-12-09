import csv
from sqlalchemy.orm import Session
from pathlib import Path
from app.models.region import Region
from app.schemas.weather import SimpleWeather
from app.utils.weather import is_good_weather, is_good_weather_from_avg
from app.utils.convert_address import convert_address_to_coordinates
from app.services.weather_service import get_avg_weather_summary, get_daily_weather_vc

CSV_PATH = Path(__file__).resolve().parent.parent.parent / "data" / "avgWeather_with_fullname.csv"

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


def candidates_from_address(address: str) -> list[str]:
    parts = address.strip().split()
    cands = []
    for i in range(len(parts), 1, -1):  # 예: [전체, '인천광역시 중구', '인천광역시']
        cands.append(" ".join(parts[:i]))
    return cands

async def get_weather_info_for_schedule(address: str, date_str: str):
    """
    avg_weather: CSV에서 평년 '기온(℃)'(평균기온), '강수량\n(mm)'(강수량)을 읽어온 dict
    predicted_temperature: 추후 예보 붙일 자리, 지금은 None
    """
    avg_weather = None

    month = int(date_str[5:7])
    day = int(date_str[8:10])
    keys = candidates_from_address(address)

    if CSV_PATH.exists():
        with CSV_PATH.open(encoding="cp949") as f:
            reader = csv.DictReader(f)

            for row in reader:
                full = (row.get("full_name") or "").strip()
                if full not in keys:
                    continue

                # CSV에서 '월', '날짜' 값은 float/문자열일 수 있으므로 안전하게 변환
                try:
                    row_month = int(float(row.get("월", 0)))
                    row_day = int(float(row.get("날짜", 0)))
                except ValueError:
                    continue

                if row_month != month or row_day != day:
                    continue

                # 여기서 매칭 성공
                t_raw = row.get("기온(℃)", "")
                p_raw = row.get("강수량\n(mm)", "")

                try:
                    t = float(t_raw) if t_raw != "" else None
                except ValueError:
                    t = None
                try:
                    p = float(p_raw) if p_raw != "" else None
                except ValueError:
                    p = None

                avg_weather = {"기온(℃)": t, "강수량(mm)": p}
                break

    return {
        "avg_weather": avg_weather,
        "predicted_temperature": None,
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
