# app/models/follow.py
from sqlalchemy import Column, BigInteger, TIMESTAMP, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base  # 여기서 Base 임포트
from app.models.user import User  # User 클래스 import

class Follow(Base):
    __tablename__ = "follows"

    follower_id = Column(BigInteger, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    following_id = Column(BigInteger, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    created_at = Column(TIMESTAMP, server_default="CURRENT_TIMESTAMP")

    follower = relationship(User, foreign_keys=[follower_id])
    following = relationship(User, foreign_keys=[following_id])
