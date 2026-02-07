from sqlalchemy import Column, Integer, String, Boolean, text
from sqlalchemy.orm import relationship
from database import Base

class InsightClass(Base):
    __tablename__ = "insight_classes"

    insight_class_id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False, index=True)
    is_builtin = Column(Boolean, nullable=False, server_default=text("true"))

    # relations
    user_insight_prefs = relationship("UserInsightPref", back_populates="insight_class")
    insights = relationship("Insight", back_populates="insight_class")
