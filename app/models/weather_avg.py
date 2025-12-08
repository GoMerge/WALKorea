from sqlalchemy import Column, BigInteger, Float, String, Date, Boolean
from sqlalchemy.orm import declarative_base

Base = declarative_base()

class AvgWeather(Base):
    __tablename__ = "avg_weather"

    stat_id = Column(BigInteger, primary_key=True)
    place_id = Column(BigInteger, index=True)
    month = Column(Float)
    day = Column(Float)
    avg_temperature = Column(Float)
    avg_precipitation = Column(Float)
    avg_humidity = Column(Float)
    wind_speed = Column(Float)
    cloud_percent = Column(Float)
    weather_condition = Column(String(50))
