from sqlalchemy import Column, Integer, Boolean, String, Date, Numeric, ForeignKey, text, UniqueConstraint
from sqlalchemy.orm import relationship
from database import Base

class Income(Base):
    __tablename__ = "income"

    income_id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False)
    date = Column(Date, nullable=False)
    bulk = Column(Boolean, nullable=False, server_default=text("false"))
    source = Column(String(255), nullable=False)
    amount = Column(Numeric(12, 2), nullable=False)
    currency = Column(String(100), nullable=False)
    recurrence_series_id = Column(Integer, ForeignKey("recurrence_series.series_id", ondelete="SET NULL"), 
                                        nullable=True, index=True)

    # relations
    user = relationship("User", back_populates="income")
    recurrence_series = relationship("RecurrenceSeries", back_populates="income")

    # constraints
    __table_args__ = (
    UniqueConstraint(                  # avoid duplicate insertion
        "user_id",
        "recurrence_series_id",
        "date",
        name="uq_income_series_date"
    )
)