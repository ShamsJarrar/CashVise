from pydantic import BaseModel
from datetime import date
from decimal import Decimal
from typing import Optional

class ExpenseBase(BaseModel):
    date: date
    bulk: bool
    expense_category: str
    currency: Optional[str] = None
    original_amount: Decimal
    recurrence_series_id: Optional[int] = None

class ExpenseCreate(ExpenseBase):
    pass

class ExpenseResponse(ExpenseBase):
    expense_id: int
    user_id: int
    usd_amount: Decimal
    fx_rate_to_usd: Optional[Decimal] = None
    fx_date: Optional[date] = None
    recurrence_series_id: Optional[int] = None

    class Config:
        from_attributes = True

class ExpenseUpdate(BaseModel):
    new_date: Optional[date] = None
    bulk: Optional[bool] = None
    expense_category: Optional[str] = None
    currency: Optional[str] = None
    original_amount: Optional[Decimal] = None