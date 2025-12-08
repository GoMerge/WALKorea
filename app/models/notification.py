from sqlalchemy import Column, BigInteger, String, Boolean, DateTime, ForeignKey
from app.database import Base

class Notification(Base):
    __tablename__ = "notifications"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, ForeignKey("users.id"), nullable=True)

    type = Column(String(50), nullable=False)
    message = Column(String(255), nullable=False)
    data = Column(String(255), nullable=True)
    is_read = Column(Boolean, default=False)
    created_at = Column(DateTime, nullable=True)
