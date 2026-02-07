from sqlalchemy import Column, Integer, ForeignKey, DateTime, func
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import JSONB
from database import Base

class Insight(Base):
    __tablename__ = "insights"

    insight_id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False)
    generated_on = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    insight_class_id = Column(Integer, ForeignKey("insight_classes.insight_class_id", ondelete="CASCADE"), nullable=False)
    raw_tool_payload = Column(JSONB, nullable=False)
    llm_insights = Column(JSONB, nullable=False)

    # relations
    user = relationship("User", back_populates="insights")
    insight_class = relationship("InsightClass", back_populates="insights")
