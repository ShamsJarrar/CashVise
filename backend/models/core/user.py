from sqlalchemy import Column, Integer, String, Boolean, DateTime
from sqlalchemy.orm import relationship
from database import Base

class User(Base):
    __tablename__ = "users"

    user_id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, nullable=False)
    password = Column(String(255), nullable=False)
    name = Column(String(100), nullable=False)
    country = Column(String(100), nullable=False)
    city = Column(String(100))
    preferred_currency = Column(String(100), nullable=False)

    # email verification
    is_verified = Column(Boolean, default=False)
    otp_code = Column(String(255), nullable=True)
    otp_expiration = Column(DateTime(timezone=True), nullable=True)

    # relations
    user_insight_prefs = relationship("UserInsightPref", back_populates="user")
    expenses = relationship("Expense", back_populates="user")
    income = relationship("Income", back_populates="user")
    recurrence_series = relationship("RecurrenceSeries", back_populates="user")
    insights = relationship("Insight", back_populates="user")
    forecasts = relationship("Forecast", back_populates="user")

    billing_customer = relationship("BillingCustomer", back_populates="user")
    subscriptions = relationship("Subscription", back_populates="user")