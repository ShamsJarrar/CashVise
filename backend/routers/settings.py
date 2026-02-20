from fastapi import APIRouter, HTTPException, status, Depends
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from sqlalchemy import and_
from dependencies import get_db, get_current_user
from models.core.user import User
from models.core.user_insight_pref import UserInsightPref
from models.core.insight_class import InsightClass
from schemas.core.user import UserResponse, UserUpdate
from schemas.core.user_insight_pref import UserInsightPrefUpdate, UserInsightPrefResponse
from utils.logger import logger
from typing import List

router = APIRouter(prefix='/settings', tags=["Settings"])


@router.patch('/update-user-info', response_model=UserResponse)
def update_user_info(
    updated_info: UserUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):

    updated = False
    
    if (updated_info.name is not None) and (updated_info.name != ""):
        user.name = updated_info.name
        updated = True
    
    if (updated_info.country is not None) and (updated_info.country != ""):
        user.country =  updated_info.country
        updated = True
    
    if (updated_info.city is not None) and (updated_info.city != ""):
        user.city = updated_info.city
        updated = True
    
    if (updated_info.preferred_currency is not None) and (updated_info.preferred_currency != ""):
        user.preferred_currency = updated_info.preferred_currency
        updated = True
    
    if not updated:
        logger.warning("User did not update their profile info")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "status": "NO_FIELDS_UPDATED",
                "message": "No profile fields were updated"
            }
        )
    
    db.commit()
    db.refresh(user)
    logger.info(f"User {user.user_id} updated their info")
    return user


@router.get('/user-insight-prefs', response_model=List[UserInsightPrefResponse])
def get_user_prefs(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):

    builtin_insight_classes = (         # return user pref for all builtin classes
        db.query(
            InsightClass.insight_class_id,
            InsightClass.key,
            InsightClass.name,
            InsightClass.is_builtin,
            UserInsightPref.enable
        )
        .outerjoin(
            UserInsightPref,
            and_(
                UserInsightPref.user_id == user.user_id,
                UserInsightPref.insight_class_id == InsightClass.insight_class_id
            )
        )
        .filter(InsightClass.is_builtin == True)
        .order_by(InsightClass.insight_class_id)
        .all()
    )

    logger.info("User prefs are loaded")
    return [
        UserInsightPrefResponse(
            insight_class_id=ip.insight_class_id,
            key=ip.key,
            name=ip.name,
            is_builtin=ip.is_builtin,
            enable=True if ip.enable is None else ip.enable
        )
        for ip in builtin_insight_classes
    ]


@router.patch('/user-insight-prefs', status_code=status.HTTP_200_OK)
def update_user_prefs(
    user_updates: UserInsightPrefUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):

    if not user_updates.updates:
        logger.warning("No updates provided")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "status": "NO_UPDATES_PROVIDED",
                "message": "Please provide updates"
            }
        )
    
    keys = [u.key for u in user_updates.updates]
    insight_classes = (
            db.query(InsightClass).filter(
                InsightClass.key.in_(keys), 
                InsightClass.is_builtin == True         # For now only builtin classes
            ).all()
    )

    get_class_by_key = {c.key: c for c in insight_classes}
    missing = [k for k in keys if k not in get_class_by_key]
    if missing:
        logger.warning("Invalid insight class key provided")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "status": "INVALID_CLASS_KEYS",
                "messages": "Invalid insight class keys are provided"
            }
        )


    class_ids = [c.insight_class_id for c in insight_classes]
    existing_user_prefs = (
        db.query(UserInsightPref).filter(
            UserInsightPref.insight_class_id.in_(class_ids),
            UserInsightPref.user_id == user.user_id
        ).all()
    )

    get_pref_by_class_id = {p.insight_class_id: p for p in existing_user_prefs}

    for u in user_updates.updates:
        key = u.key
        insight_class = get_class_by_key[key]
        pref_exists = get_pref_by_class_id.get(insight_class.insight_class_id)

        if pref_exists:
            pref_exists.enable = u.enable
        else:
            new_user_pref = UserInsightPref(
                user_id=user.user_id,
                insight_class_id=insight_class.insight_class_id,
                enable=u.enable
            )
            db.add(new_user_pref)
            get_pref_by_class_id[insight_class.insight_class_id] = new_user_pref
        
    db.commit()
    logger.info(f"User {user.user_id}'s prefs updated successfully")
    return {
            "status": "PREFS_UPDATED",
            "message": "User insight prefs updated successfully."
        }






