from pydantic import BaseModel
from typing import List
from .insight_class import InsightClass

class UserInsightPrefUpdateItem(BaseModel):
    key: str       
    enable: bool

class UserInsightPrefUpdate(BaseModel):
    updates: List[UserInsightPrefUpdateItem]

class UserInsightPrefResponse(InsightClass):
    enable: bool