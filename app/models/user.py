from sqlalchemy import Column, String, BigInteger, Date, TIMESTAMP, DateTime, Boolean
from sqlalchemy.sql import func
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class User(Base):
    __tablename__ = "users"

    id = Column(BigInteger, primary_key=True, index=True, autoincrement=True)
    userid = Column(String(50), unique=True, index=True, nullable=True)
    email = Column(String(100), unique=True, index=True, nullable=False)
    pw_hash = Column(String(255), nullable=True)
    refresh_token_hash = Column(String(255), nullable=True)
    name = Column(String(100), nullable=True)
    phonenum = Column(String(20), unique=True, nullable=False)
    birthday = Column(Date, nullable=True)
    gender = Column(String(10), nullable=True)
    role = Column(String(50), default='user')
    provider = Column(String(50), nullable=True)
    provider_id = Column(String(100), nullable=True)
    nickname = Column(String, unique=True, nullable=True)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), onupdate=func.now())
    deleted_at = Column(DateTime, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)

    @property
    def active(self):
        return self.is_active and self.deleted_at is None
    