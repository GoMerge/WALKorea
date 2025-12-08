from typing import Optional

def get_season(month: int) -> str:
    if month in [3, 4, 5]:
        return "spring"
    elif month in [6, 7, 8]:
        return "summer"
    elif month in [9, 10, 11]:
        return "autumn"
    else:
        return "winter"

month_weather_criteria = {
    1:  {"temp_range": (-3, 3),   "max_precip": 1, "max_cloud": 60, "max_wind": 6, "hum_range": (25, 70)},
    2:  {"temp_range": (-2, 5),   "max_precip": 1, "max_cloud": 60, "max_wind": 6, "hum_range": (25, 70)},
    3:  {"temp_range": (4, 12),   "max_precip": 2, "max_cloud": 60, "max_wind": 6, "hum_range": (30, 75)},
    4:  {"temp_range": (9, 17),   "max_precip": 2, "max_cloud": 60, "max_wind": 6, "hum_range": (35, 75)},
    5:  {"temp_range": (14, 22),  "max_precip": 3, "max_cloud": 60, "max_wind": 6, "hum_range": (35, 75)},
    6:  {"temp_range": (19, 26),  "max_precip": 4, "max_cloud": 70, "max_wind": 7, "hum_range": (45, 80)},
    7:  {"temp_range": (22, 29),  "max_precip": 5, "max_cloud": 80, "max_wind": 7, "hum_range": (50, 85)},
    8:  {"temp_range": (22, 29),  "max_precip": 5, "max_cloud": 80, "max_wind": 7, "hum_range": (50, 85)},
    9:  {"temp_range": (18, 25),  "max_precip": 4, "max_cloud": 70, "max_wind": 7, "hum_range": (40, 80)},
    10: {"temp_range": (11, 19),  "max_precip": 2, "max_cloud": 60, "max_wind": 6, "hum_range": (35, 75)},
    11: {"temp_range": (5, 12),   "max_precip": 2, "max_cloud": 60, "max_wind": 6, "hum_range": (30, 75)},
    12: {"temp_range": (-1, 5),   "max_precip": 1, "max_cloud": 60, "max_wind": 6, "hum_range": (25, 70)},
}


def is_good_weather(weather) -> bool:
    m = weather.month
    c = month_weather_criteria.get(m)
    if not c:
        return False

    if not (c["temp_range"][0] <= weather.avg_temperature <= c["temp_range"][1]):
        return False
    if weather.avg_precipitation > c["max_precip"]:
        return False
    if weather.cloud_percent > c["max_cloud"]:
        return False
    if weather.wind_speed > c["max_wind"]:
        return False
    if not (c["hum_range"][0] <= weather.avg_humidity <= c["hum_range"][1]):
        return False

    return True



def is_good_weather_from_avg(
    avg_tmin: Optional[float],
    avg_tmax: Optional[float],
    today_tmin: Optional[float],
    today_tmax: Optional[float],
    max_diff: float = 2.0,
) -> bool:
    """평년 최저/최고와 오늘(예보) 최저/최고 차이 체크"""
    if avg_tmin is None or avg_tmax is None:
        return False
    if today_tmin is None or today_tmax is None:
        return False

    if abs(today_tmin - avg_tmin) > max_diff:
        return False
    if abs(today_tmax - avg_tmax) > max_diff:
        return False
    return True