from sqlalchemy import Column, Integer, String, Numeric, Date, DateTime, func, UniqueConstraint
from database import Base

class FXRate(Base):
    __tablename__ = "fx_rates"

    rate_id = Column(Integer, primary_key=True, index=True)
    original_currency = Column(String(100), nullable=False)
    to_currency = Column(String(100), nullable=False)
    rate = Column(Numeric(18,8), nullable=False)
    rate_date = Column(Date, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # constraints
    __table_args__ = (
        UniqueConstraint(
            "original_currency",
            "to_currency",
            "rate_date",
            name="uq_fx_rates_rate_date"
        ),
    )
