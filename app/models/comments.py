
from sqlalchemy import Column, BigInteger, String, ForeignKey, TIMESTAMP, func,Text
from sqlalchemy.orm import relationship
from app.database import Base


class Comment(Base):
    __tablename__ = "comments"
    
    id = Column(BigInteger, primary_key=True, index=True)
    place_id = Column(BigInteger, ForeignKey("places.id"), nullable=False)
    user_id = Column(BigInteger, ForeignKey("users.id"), nullable=False)
    content = Column(Text, nullable=False)
    created_at = Column(TIMESTAMP, default=func.now())
    
    # 관계 설정 (User, Place 모델에 back_populates 추가 필요)
    user = relationship("User", back_populates="comments")
    place = relationship("Place", back_populates="comments")