from pydantic import BaseModel
from typing import List

class UserInsightPrefUpdateItem(BaseModel):
    key: str       
    enable: bool

class UserInsightPrefUpdate(BaseModel):
    updates: List[UserInsightPrefUpdateItem]

class UserInsightPrefResponse(BaseModel):
    insight_class_id: int
    key: str
    name: str
    is_builtin: bool
    enable: bool