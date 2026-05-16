from pydantic import BaseModel
from typing import List, Dict
from decimal import Decimal
from datetime import date

class FXRate(BaseModel):
    fx_date: date
    rate: Decimal

class ConversionResponse(BaseModel):
    fx_date: date
    rate: Decimal
    amount: Decimal

class SupportedCodes(BaseModel):
    codes: Dict