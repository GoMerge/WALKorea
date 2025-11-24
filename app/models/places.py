from sqlalchemy import (
    Column, BigInteger, String, Text, Integer, DECIMAL, Boolean, 
    JSON, TIMESTAMP, Date, Float, DateTime, ForeignKey)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


# 공통 저장
class Place(Base):
    """
    공통 관광지/명소/축제/숙박/음식점 데이터를 저장하는 테이블
    (TourAPI detailCommon 기반)
    """
    __tablename__ = "places"

    id = Column(BigInteger, primary_key=True, autoincrement=True) # 내부 pk
    content_id = Column(String(50), unique=True, nullable=False)  # TourAPI contentid
    content_type_id = Column(Integer, nullable=False)  # 관광 타입

    title = Column(String(300), nullable=False) # 관광지명

    # 주소 정보
    addr1 = Column(String(500))
    addr2 = Column(String(500))
    areacode = Column(String(10))
    sigungucode = Column(String(10))

    # 위치 정보
    latitude = Column(Float)
    longitude = Column(Float)

    # 카테고리 3단계
    cat1 = Column(String(10))
    cat2 = Column(String(20))
    cat3 = Column(String(20))

    # 개요/이미지/기본 정보
    overview = Column(Text)
    first_image = Column(String(500))
    first_image2 = Column(String(500))

    # 기타 메타데이터

    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())

    # Relationships
    details = relationship("PlaceDetail", back_populates="place", uselist=False)
    images = relationship("PlaceImage", back_populates="place", cascade="all, delete-orphan")
    festival = relationship("Festival", back_populates="place", uselist=False)


#
class PlaceDetail(Base):
    """
    detailIntro + detailInfo 등
    타입별 상세 데이터를 JSON으로 저장
    """
    __tablename__ = "place_details"

    id = Column(BigInteger, primary_key=True, index=True)
    place_id = Column(BigInteger, ForeignKey("places.id"), nullable=False)

    detail_json = Column(JSON)  # 구조가 관광타입마다 다르므로 JSON으로 저장

    place = relationship("Place", back_populates="details")

#
class PlaceImage(Base):
    """
    detailImage 이미지 목록 저장
    1:N 관계
    """
    __tablename__ = "place_images"

    id = Column(BigInteger, primary_key=True, index=True)
    place_id = Column(BigInteger, ForeignKey("places.id"), nullable=False)

    image_url = Column(String(500))
    thumbnail_url = Column(String(500))

    place = relationship("Place", back_populates="images")

class Festival(Base):
    """
    contentTypeId = 15 (행사/축제) 전용 테이블
    detailIntro에서 얻는 전용 필드 저장
    """
    __tablename__ = "festivals"

    id = Column(BigInteger, primary_key=True, index=True)
    place_id = Column(BigInteger, ForeignKey("places.id"), nullable=False)

    event_start_date = Column(Date)  # YYYYMMDD
    event_end_date = Column(Date)
    event_place = Column(String(500))
    playtime = Column(String(200))
    agelimit = Column(String(100))

    place = relationship("Place", back_populates="festival")