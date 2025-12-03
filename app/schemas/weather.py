from pydantic import BaseModel
from datetime import date
from dataclasses import dataclass

@dataclass
class SimpleWeather:
    month: int
    avg_temperature: float
    avg_precipitation: float
    cloud_percent: float
    wind_speed: float
    avg_humidity: float

class WeatherCurrentResponse(BaseModel):
    region_id: int
    weather_date: date
    temperature: float
    precipitation: float | None = None
    humidity: float | None = None
    condition: str

    class Config:
        from_attributes = True


class CalendarWeatherItem(BaseModel):
    address: str
    date: str   # "YYYY-MM-DD"


class CalendarWeatherResult(BaseModel):
    date: str
    address: str
    is_good: bool | None = None
    avg_temp: float | None = None
    precip_mm: float | None = None


class CalendarWeatherResponse(BaseModel):
    results: list[CalendarWeatherResult]