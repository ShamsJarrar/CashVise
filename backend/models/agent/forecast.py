from sqlalchemy import Column, Integer, ForeignKey, DateTime, func
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import JSONB
from database import Base

class Forecast(Base):
    __tablename__ = "forecasts"

    forecast_id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False)
    generated_on = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    forecast = Column(JSONB, nullable=False)

    # relations
    user = relationship("User", back_populates="forecasts")