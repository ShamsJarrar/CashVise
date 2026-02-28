from pydantic import BaseModel
from typing import List
from decimal import Decimal

class FXRate(BaseModel):
    rate: Decimal

class ConversionResponse(BaseModel):
    rate: Decimal
    amount: Decimal

class SupportedCodes(BaseModel):
    codes: List[List[str]]