from pydantic import BaseModel
from typing import List

class UserInsightPrefUpdateItem(BaseModel):
    key: str       
    enabled: bool

class UserInsightPrefUpdate(BaseModel):
    updates: List[UserInsightPrefUpdateItem]

class UserInsightPrefResponse(BaseModel):
    insight_class_id: int
    key: str
    name: str
    is_builtin: bool
    enabled: bool