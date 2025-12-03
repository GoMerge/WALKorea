from sqlalchemy import Column, BigInteger, ForeignKey, JSON
from sqlalchemy.orm import relationship
from app.database import Base

class UserProfile(Base):
    __tablename__ = "user_profile"
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, ForeignKey("users.id"), nullable=False, unique=True)
    preferences = Column(JSON, nullable=False)
    
    user = relationship("User", backref="profile")
