from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, func, UniqueConstraint
from sqlalchemy.orm import relationship
from app.database import Base

class Region(Base):
    __tablename__ = "regions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    code = Column(String(50), unique=True, nullable=False)
    name = Column(String(100), nullable=False)
    parent_id = Column(Integer, ForeignKey("regions.id"), nullable=True)
    level = Column(Integer, nullable=False, index=True)
    sido = Column(String(30), nullable=True)
    gungu = Column(String(30), nullable=True)
    myeon_eupdong = Column(String(30), nullable=True)
    ri_dong = Column(String(30), nullable=True)
    full_name = Column(String(255), nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    parent = relationship("Region", remote_side=[id], backref="children")

    __table_args__ = (UniqueConstraint("code", name="uq_regions_code"),)
