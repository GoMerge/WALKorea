from sqlalchemy import Column, BigInteger, DateTime, PrimaryKeyConstraint, func
from app.database import Base

class Favorite(Base):
    __tablename__ = "favorites"

    user_id = Column(BigInteger, nullable=False)
    place_id = Column(BigInteger, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        PrimaryKeyConstraint("user_id", "place_id", name="pk_favorites"),
    )
