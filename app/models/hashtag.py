# app/models/hashtag.py
from sqlalchemy import Column, BigInteger, String, ForeignKey, TIMESTAMP, func
from sqlalchemy.orm import relationship
from app.database import Base

class Tag(Base):
    __tablename__ = "tags"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    name = Column(String(100), unique=True, nullable=False)  # 실제 해시태그 이름
    slug = Column(String(100), unique=True, nullable=False)  # 검색용
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())

    places = relationship("PlaceTag", back_populates="tag", cascade="all, delete-orphan")


class PlaceTag(Base):
    __tablename__ = "place_tags"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    place_id = Column(BigInteger, ForeignKey("places.id"), nullable=False)
    tag_id = Column(BigInteger, ForeignKey("tags.id"), nullable=False)

    place = relationship("Place", back_populates="hashtags")
    tag = relationship("Tag", back_populates="places")

