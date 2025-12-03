# app/models/weather_current.py
from sqlalchemy import Column, BigInteger, Integer, Date, Float, String, ForeignKey, Index
from sqlalchemy.orm import relationship
from app.database import Base

class WeatherCurrent(Base):
    __tablename__ = "weather_current"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    region_id = Column(Integer, ForeignKey("regions.id"), nullable=False)
    weather_date = Column(Date, nullable=False)
    temperature = Column(Float, nullable=False)
    precipitation = Column(Float)
    humidity = Column(Float)
    condition = Column(String(50))

    # 관계 설정
    region = relationship("Region", backref="weather_current")

    __table_args__ = (
        Index("idx_weather_region_date", "region_id", "weather_date"),
    )

    def __repr__(self):
        return f"<WeatherCurrent(region_id={self.region_id}, date={self.weather_date}, temp={self.temperature})>"

    def to_dict(self):
        return {
            "region_id": self.region_id,
            "weather_date": self.weather_date.isoformat(),
            "temperature": self.temperature,
            "condition": self.condition,
        }