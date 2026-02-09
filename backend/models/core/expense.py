from sqlalchemy import Column, Integer, Boolean, String, Date, Numeric, ForeignKey, text, UniqueConstraint
from sqlalchemy.orm import relationship
from database import Base

class Expense(Base):
    __tablename__ = "expenses"

    expense_id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False)
    date = Column(Date, nullable=False)
    bulk = Column(Boolean, nullable=False, server_default=text("false"))
    expense_category = Column(String(255), nullable=False)
    preferred_currency_amount = Column(Numeric(12, 2), nullable=False)
    usd_amount = Column(Numeric(12, 2), nullable=False)
    recurrence_series_id = Column(Integer, ForeignKey("recurrence_series.series_id", ondelete="SET NULL"), 
                                        nullable=True, index=True)

    # relations
    user = relationship("User", back_populates="expenses")
    recurrence_series = relationship("RecurrenceSeries", back_populates="expenses")

    # constraints
    __table_args__ = (
    UniqueConstraint(                  # avoid duplicate insertion
        "user_id",
        "recurrence_series_id",
        "date",
        name="uq_expense_series_date"
    ),
)