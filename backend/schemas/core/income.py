from pydantic import BaseModel
from datetime import date
from decimal import Decimal
from typing import Optional

class IncomeBase(BaseModel):
    date: date
    bulk: bool
    source: str
    currency: Optional[str] = None
    original_amount: Decimal
    recurrence_series_id: Optional[int] = None

class IncomeCreate(IncomeBase):
    pass

class IncomeResponse(IncomeBase):
    income_id: int
    user_id: int
    usd_amount: Decimal
    fx_rate_to_usd: Optional[Decimal] = None
    fx_date: Optional[date] = None
    recurrence_series_id: Optional[int] = None

    class Config:
        from_attributes = True
    
class IncomeUpdate(BaseModel):
    new_date: Optional[date] = None
    bulk: Optional[bool] = None
    source: Optional[str] = None
    currency: Optional[str] = None
    original_amount: Optional[Decimal] = None