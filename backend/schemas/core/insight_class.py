from pydantic import BaseModel

class InsightClass(BaseModel):
    insight_class_id: int
    key: str
    name: str
    is_builtin: bool

class InsightClassReponse(InsightClass):
    class Config:
        from_attributes = True