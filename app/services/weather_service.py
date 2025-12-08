import os
import pandas as pd
from dotenv import load_dotenv
import aiohttp
import datetime as dt, datetime
from typing import Dict, Any, Optional
from app.utils.convert_address import convert_address_to_coordinates
from app.utils.redis_client import get_cached, set_cached

load_dotenv()

OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY")
VISUALCROSSING_API_KEY = os.getenv("VISUALCROSSING")

if not OPENWEATHER_API_KEY:
    raise RuntimeError("OPENWEATHER_API_KEY 환경변수가 설정되어 있지 않습니다.")
if not VISUALCROSSING_API_KEY:
    raise RuntimeError("VISUALCROSSING 환경변수가 설정되어 있지 않습니다.")

AVG_CSV_PATH = "data/avgWeather_with_fullname.csv"

_df_avg_weather = None

BASE_VC_URL = "https://weather.visualcrossing.com/VisualCrossingWebServices/rest/services/timeline"


async def fetch_daily_from_visualcrossing(address: str) -> Dict[str, Any]:
    if not VISUALCROSSING_API_KEY:
        raise RuntimeError("VISUALCROSSING 환경변수가 설정되어 있지 않습니다.")

    coords = convert_address_to_coordinates(address)
    if coords is None:
        raise ValueError("좌표 변환 실패: 입력 주소를 확인해주세요.")
    lat, lon = coords

    url = BASE_VC_URL
    location = f"{lat},{lon}"

    params = {
        "location": location,
        "key": VISUALCROSSING_API_KEY,
        "unitGroup": "metric",
        "include": "days",
        "lang": "ko",
        "elements": "datetime,tempmax,tempmin,temp,conditions,icon",
        "startDate": "today",
        "endDate": "next5days",
    }

    async with aiohttp.ClientSession() as session:
        async with session.get(url, params=params, timeout=10) as response:
            response.raise_for_status()
            raw: Dict[str, Any] = await response.json()

    days_raw = raw.get("days", [])
    daily: list[Dict[str, Any]] = []
    for item in days_raw[:6]:
        date_str = item.get("datetime")
        temp = item.get("temp")
        tmax = item.get("tempmax")
        tmin = item.get("tempmin")
        icon = item.get("icon")  
        
        if temp is None and tmax is not None and tmin is not None:
            temp = (tmax + tmin) / 2.0
        desc = item.get("conditions")
        
        icon_map = {
            "rain": "rain", "snow": "snow", "sleet": "sleet",
            "cloudy": "cloudy", "partly-cloudy-day": "cloudy", 
            "clear-day": "clear", "partly-cloudy-night": "cloudy"
        }
        daily.append({
            "date": date_str,
            "temp_min": tmin,
            "temp_max": tmax,
            "icon": icon_map.get(icon, "clear"),  # 이제 icon 정의됨
        })

    return {"daily": daily}


async def get_daily_weather_vc(address: str) -> Dict[str, Any]:
    cache_key = f"vc_daily:{address}"
    cached = await get_cached(cache_key)
    if cached:
        return cached

    data = await fetch_daily_from_visualcrossing(address)
    await set_cached(cache_key, data, expire_seconds=1800)  
    return data


async def fetch_daily_from_openweather(address: str) -> Dict[str, Any]:
    coords = convert_address_to_coordinates(address)
    if coords is None:
        raise ValueError("좌표 변환 실패: 입력 주소를 확인해주세요.")

    lat, lon = coords

    url = "https://api.openweathermap.org/data/2.5/onecall"
    params = {
        "lat": lat,
        "lon": lon,
        "appid": OPENWEATHER_API_KEY,
        "units": "metric",
        "lang": "kr",
        "exclude": "minutely,hourly,alerts",
    }

    async with aiohttp.ClientSession() as session:
        async with session.get(url, params=params, timeout=10) as response:
            response.raise_for_status()
            raw = await response.json()

    if "daily" not in raw:
        current = raw.get("current") or {}
        return {
            "daily": [
                {
                    "date": dt.datetime.utcfromtimestamp(current.get("dt", 0)).date().isoformat(),
                    "temp": current.get("temp"),
                    "desc": (current.get("weather") or [{}])[0].get("description"),
                }
            ]
        }

    days = []
    for item in raw["daily"][:7]:
        date_str = dt.datetime.utcfromtimestamp(item.get("dt", 0)).date().isoformat()
        if isinstance(item.get("temp"), dict):
            temp_day = item["temp"].get("day")
        else:
            temp_day = item.get("temp")

        desc = (item.get("weather") or [{}])[0].get("description")

        days.append(
            {
                "date": date_str,
                "temp": temp_day,
                "desc": desc,
            }
        )

    return {"daily": days}


async def fetch_weather_from_openweather(address: str) -> Dict[str, Any]:
    coords = convert_address_to_coordinates(address)
    if coords is None:
        raise ValueError("좌표 변환 실패: 입력 주소를 확인해주세요.")

    lat, lon = coords
    url = "https://api.openweathermap.org/data/2.5/weather"
    params = {
        "lat": lat,
        "lon": lon,
        "appid": OPENWEATHER_API_KEY,
        "units": "metric",
        "lang": "kr",
    }
    async with aiohttp.ClientSession() as session:
        async with session.get(url, params=params, timeout=10) as response:
            response.raise_for_status()
            return await response.json()


async def get_daily_weather(address: str) -> Dict[str, Any]:
    cache_key = f"weather_daily:{address}"
    cached = await get_cached(cache_key)
    if cached:
        return cached

    data = await fetch_daily_from_openweather(address)
    await set_cached(cache_key, data, expire_seconds=3600)
    return data


async def get_weather(city_name: str) -> Dict[str, Any]:
    cache_key = f"weather:{city_name}"
    cached = await get_cached(cache_key)
    if cached:
        return cached

    weather_data = await fetch_weather_from_openweather(city_name)
    await set_cached(cache_key, weather_data, expire_seconds=3600)
    return weather_data


def load_avg_weather_data() -> pd.DataFrame:
    global _df_avg_weather
    if _df_avg_weather is None:
        df = pd.read_csv(AVG_CSV_PATH, encoding="cp949", low_memory=False)
        num_cols = [4, 5, 6, 7, 8, 9, 11, 12]
        for c in num_cols:
            df.iloc[:, c] = pd.to_numeric(df.iloc[:, c], errors="coerce")

        df["full_name"] = df["full_name"].astype(str)
        df["month"] = pd.to_numeric(df["월"], errors="coerce")
        df["day"] = pd.to_numeric(df["날짜"], errors="coerce")
        df["temperature"] = pd.to_numeric(df["기온(℃)"], errors="coerce")

        precip_col = None
        for cand in ["강수량(mm)", "강수량\n(mm)", "강수량 (mm)"]:
            if cand in df.columns:
                precip_col = cand
                break

        if precip_col:
            df["precipitation"] = pd.to_numeric(df[precip_col], errors="coerce")
        else:
            df["precipitation"] = 0.0

        _df_avg_weather = df

    return _df_avg_weather


def normalize_address_for_match(address: str) -> str:
    if not address:
        return ""
    parts = str(address).split()
    if len(parts) >= 2 and ("시" in parts[0] or "도" in parts[0]):
        return " ".join(parts[:2])
    return parts[0]


def find_closest_fullname(target: str, df: pd.DataFrame) -> str | None:
    target = normalize_address_for_match(target).strip()
    if not target:
        return None

    exact = df[df["full_name"] == target]
    if not exact.empty:
        return target

    contains = df[df["full_name"].str.contains(target, na=False)]
    if not contains.empty:
        return contains.iloc[0]["full_name"]

    contains_rev = df[df["full_name"].apply(lambda x: target in str(x))]
    if not contains_rev.empty:
        return contains_rev.iloc[0]["full_name"]

    return None


def find_avg_weather_by_address_and_date(address: str, year: int, month: int, day: int) -> Optional[Dict[str, Any]]:
    df = load_avg_weather_data()

    candidates = df[df["full_name"].notnull() & df["full_name"].str.contains(address.split()[0][:2], na=False)]
    if candidates.empty:
        return None

    filtered = candidates[(candidates["월"] == month) & (candidates["날짜"] == day)]
    if filtered.empty:
        filtered = candidates

    row = filtered.iloc[0]

    return {
        "기온(℃)": row.get("기온(℃)", None),
        "강수량(mm)": row.get("강수량\n(mm)", None),
        "상대습도(%)": row.get("상대습도(%)", None),
        "일조시간(hr)": row.get("일조시간\n(hr)", None),
        "지점명": row.get("지점명", None),
        "주소": row.get("full_name", None),
    }


async def get_avg_weather_summary(address: str, date_str: str):
    if not address or not date_str:
        return None

    try:
        dt_obj = datetime.datetime.strptime(date_str, "%Y-%m-%d")
        month, day = dt_obj.month, dt_obj.day
        
        df = load_avg_weather_data()
        closest_full = find_closest_fullname(address, df)
        if not closest_full:
            return None

        # month/day 정확히 매칭 → 월 평균 fallback
        exact_match = df[
            (df["full_name"] == closest_full) & 
            (df["month"] == month) & 
            (df["day"] == day)
        ]
        
        if exact_match.empty:
            # 같은 월 평균
            month_avg = df[
                (df["full_name"] == closest_full) & 
                (df["month"] == month)
            ]
            if month_avg.empty:
                return None
            row = month_avg.iloc[0]
        else:
            row = exact_match.iloc[0]

        return {
            "full_name": closest_full,
            "month": int(month),
            "day": int(day),
            "기온(℃)": float(row.get("temperature", 0)) if pd.notna(row.get("temperature")) else None,
            "강수량(mm)": float(row.get("precipitation", 0)) if pd.notna(row.get("precipitation")) else None,
        }
    except Exception:
        return None