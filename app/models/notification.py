from sqlalchemy import Column, BigInteger, String, Boolean, DateTime, ForeignKey
<<<<<<< HEAD
from sqlalchemy.orm import relationship
=======
>>>>>>> 1397ebca396d01ba59f35c6f7d5d14cdb9dd3b1f
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
<<<<<<< HEAD

    user = relationship("User", back_populates="notifications")
=======
>>>>>>> 1397ebca396d01ba59f35c6f7d5d14cdb9dd3b1f
