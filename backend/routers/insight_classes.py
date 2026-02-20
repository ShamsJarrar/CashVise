from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from models.core.user import User
from models.core.insight_class import InsightClass
from schemas.core.insight_class import InsightClassReponse
from dependencies import get_current_user, get_db
from utils.logger import logger
from typing import List

router = APIRouter(prefix='/insight-classes', tags=['Insight Classes'])

@router.get('/', response_model=List[InsightClassReponse])
def list_insight_classes(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    insight_classes = db.query(InsightClass).all()

    logger.info("Userrequested insight classes list")
    return insight_classes


@router.get('/{key}', response_model=InsightClassReponse)
def get_insight_class(
    key: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    insight_class = db.query(InsightClass).filter(
        InsightClass.key == key
    ).first()

    if insight_class is None:
        logger.warning("User is trying get a non-existent insight class")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "status": "INVALID_CLASS",
                "message": "The class does not exist, please use a valid key"
            }
        )
    
    logger.info(f"User {user.user_id} requested an insight class")
    return insight_class
    
