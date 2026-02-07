from sqlalchemy import Column, Integer, Boolean, Date, ForeignKey, text, Enum, CheckConstraint
from sqlalchemy.orm import relationship
from database import Base
import enum

class SeriesType(str, enum.Enum):
    EXPENSE = "EXPENSE"
    INCOME = "INCOME"

class Frequency(str, enum.Enum):
    DAILY = "DAILY"
    MONTHLY = "MONTHLY"
    YEARLY = "YEARLY"

class RecurrenceSeries(Base):
    __tablename__ = "recurrence_series"

    series_id = Column(Integer, primary_key=True, index=True)
    user_id =  Column(Integer, ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False)
    series_type = Column(Enum(SeriesType, name="series_type"), nullable=False)
    frequency = Column(Enum(Frequency, name="frequency"), nullable=False, server_default=text("'NONE'"))
    bulk = Column(Boolean, nullable=False, server_default=text("false"))
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=True)
    is_active = Column(Boolean, nullable=False, server_default=text("true"))

    # relations
    user = relationship("User", back_populates="recurrence_series")
    expenses = relationship("Expense", back_populates="recurrence_series")
    income = relationship("Income", back_populates="recurrence_series")

    # constraints
    __table_args__ = (
    CheckConstraint(
        "(bulk = false) OR (frequency IN ('MONTHLY','YEARLY'))",    # if bulk is false allow daily
        name="ck_series_bulk_frequency"
    ),
    CheckConstraint(
        "(end_date IS NULL) OR (end_date >= start_date)",   # end date should be after start date
        name="ck_series_end_after_start"
    ),
)




