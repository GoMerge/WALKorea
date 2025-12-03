from sqlalchemy import Column, BigInteger, Integer, Date, Time, String, ForeignKey, TIMESTAMP, DateTime, UniqueConstraint, func
from sqlalchemy.orm import relationship
from app.database import Base

class UserCalendar(Base):
    __tablename__ = "user_calendar"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, ForeignKey("users.id"), nullable=False)
    place_id = Column(BigInteger, ForeignKey("places.id"), nullable=True)
    event_date = Column(Date, nullable=False)
    start_time = Column(Time, nullable=True)
    end_time = Column(Time, nullable=True)
    memo = Column(String(255))
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)

    user = relationship("User", back_populates="user_calendars")  # backref 제거
    
    events = relationship("CalendarEvent", back_populates="calendar")
    places = relationship("CalendarPlace", back_populates="calendar") 
    shares = relationship("CalendarShare", back_populates="calendar")
    
class CalendarShare(Base):
    __tablename__ = "calendar_shares"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    calendar_id = Column(BigInteger, ForeignKey("user_calendar.id", ondelete="CASCADE"), nullable=False)
    follower_id = Column(BigInteger, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    shared_at = Column(DateTime, server_default=func.now())
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)

    __table_args__ = (UniqueConstraint("calendar_id", "follower_id", name="uix_calendar_follower"),)

    calendar = relationship("UserCalendar", back_populates="shares")
    follower = relationship("User")

class CalendarEvent(Base):
    __tablename__ = "calendar_events"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    calendar_id = Column(BigInteger, ForeignKey("user_calendar.id", ondelete="CASCADE"), nullable=False)
    title = Column(String(100), nullable=False)
    start_datetime = Column(DateTime, nullable=False)
    end_datetime = Column(DateTime, nullable=True)
    location = Column(String(255), nullable=True)
    description = Column(String(255), nullable=True)
    remind_minutes = Column(Integer, nullable=True)
    # ★ 추가: 공유 여부 / 원본 정보
    is_shared = Column(Integer, nullable=False, server_default="0")  # 0: 내 일정, 1: 공유로 받은 일정
    shared_from_user_id = Column(BigInteger, ForeignKey("users.id"), nullable=True)
    shared_from_event_id = Column(BigInteger, ForeignKey("calendar_events.id"), nullable=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)

    calendar = relationship("UserCalendar", back_populates="events")
    shared_from_user = relationship("User", foreign_keys=[shared_from_user_id])
    shared_from_event = relationship("CalendarEvent", remote_side=[id])

class CalendarShareRequest(Base):
    __tablename__ = "calendar_share_requests"

    id = Column(BigInteger, primary_key=True, autoincrement=True)

    # 누가, 누구에게
    from_user_id = Column(BigInteger, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    to_user_id   = Column(BigInteger, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)

    # 어떤 일정(원본)
    event_id = Column(BigInteger, ForeignKey("calendar_events.id", ondelete="CASCADE"), nullable=False)

    status = Column(String(20), nullable=False, server_default="pending")  # pending / accepted / rejected
    created_at  = Column(DateTime, server_default=func.now(), nullable=False)
    responded_at = Column(DateTime, nullable=True)

    from_user = relationship("User", foreign_keys=[from_user_id])
    to_user   = relationship("User", foreign_keys=[to_user_id])
    event     = relationship("CalendarEvent")

class CalendarPlace(Base):
    __tablename__ = "calendar_places"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    calendar_id = Column(BigInteger, ForeignKey("user_calendar.id", ondelete="CASCADE"), nullable=False)
    place_id = Column(BigInteger, ForeignKey("places.id", ondelete="CASCADE"), nullable=False)
    visit_date = Column(Date, nullable=False)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)

    calendar = relationship("UserCalendar", back_populates="places")