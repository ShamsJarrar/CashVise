from sqlalchemy import Column, Integer, Boolean, ForeignKey, text
from sqlalchemy.orm import relationship
from database import Base

class UserInsightPref(Base):
    __tablename__ = "user_insight_prefs"

    user_id = Column(Integer, ForeignKey("users.user_id", ondelete="CASCADE"), primary_key=True)
    insight_class_id = Column(Integer, ForeignKey("insight_classes.insight_class_id", ondelete="CASCADE"), primary_key=True)
    enable = Column(Boolean, nullable=False, server_default=text("true"))

    # relations
    user = relationship("User", back_populates="user_insight_prefs")
    insight_class = relationship("InsightClass", back_populates="user_insight_prefs")