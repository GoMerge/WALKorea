# app/models/follow.py
from sqlalchemy import Column, BigInteger, TIMESTAMP, ForeignKey, text
from sqlalchemy.orm import relationship
from app.database import Base  # 여기서 Base 임포트
from app.models.user import User  # User 클래스 import
from datetime import datetime

class Follow(Base):
    __tablename__ = "follows"

    follower_id = Column(BigInteger, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    following_id = Column(BigInteger, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    created_at = Column(
        TIMESTAMP,
        nullable=True,
        server_default=text("CURRENT_TIMESTAMP")
    )

    follower = relationship(User, foreign_keys=[follower_id])
    following = relationship(User, foreign_keys=[following_id])
