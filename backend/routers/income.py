from fastapi import APIRouter, Depends, HTTPException, status, Query, Response
from sqlalchemy.orm import Session
from dependencies import get_db, get_current_user, get_fx_service
from models.core.user import User
from models.core.income import Income
from schemas.core.income import IncomeCreate, IncomeResponse, IncomeUpdate
from services.fx_service import FXService
from utils.helpers import normalize_string
from utils.logger import logger
from typing import List, Optional
from datetime import date

router = APIRouter(prefix='/income', tags=['Income'])

@router.get('/', response_model=List[IncomeResponse])
def get_all_income(
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):

    date_filters = []
    if start_date is not None:
        date_filters.append(Income.date >= start_date)
    
    if end_date is not None:
        date_filters.append(Income.date <= end_date)

    income = db.query(Income).filter(
        Income.user_id == user.user_id,
        *date_filters
    ).all()

    return income


@router.get('/{income_id}', response_model=IncomeResponse)
def get_income(
    income_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):

    income = db.query(Income).filter(
        Income.income_id == income_id
    ).first()

    if income is None:
        logger.warning("User tried to fetch income using income_id, but income does not exist")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "status": "INCOME_NOT_FOUND",
                "message": "User tried to fetch nonexistent income row"
            }
        )
    
    if income.user_id != user.user_id:
        logger.warning("User is not authorized to access the income they tried to fetch")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "status": "FORBIDDEN_ACCESS_TO_INCOME",
                "message": "User is not authorized to access the income fielf"
            }
        )
    
    return income


@router.post('/', response_model=IncomeResponse)
async def add_income(
    income: IncomeCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
    fx_service: FXService = Depends(get_fx_service)
):

    if income.date > date.today():
        logger.warning("User tried to add future income.")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "status": "FUTURE_INCOME_NOT_ALLOWED",
                "message": "User is not allowed to add future income"
            }
        )
    
    if income.currency is None:
        income.currency = user.preferred_currency

    available_currencies = await fx_service.get_supported_codes()
    income.currency = normalize_string(income.currency)
    if income.currency not in available_currencies:
        logger.warning("User tried to add income with an unsupported currency")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "status": "UNSUPPORTED_CURRENCY",
                "message": "User tried to add an incomr with an unsupported currency"
            }
        )
    
    # force bulk income to be on the first day of the month if frontend didn't do it
    if income.bulk == True:
        if income.date.day != 1:
            income.date = date(income.date.year, income.date.month, 1)
    
    converted_amount_and_rate = await fx_service.convert(db, income.currency, "USD", income.original_amount, income.date)

    new_income = Income(
        user_id=user.user_id,
        date=income.date,
        bulk=income.bulk,
        source=income.source,
        currency=income.currency,
        original_amount=income.original_amount,
        usd_amount=converted_amount_and_rate['amount'],
        fx_rate_to_usd=converted_amount_and_rate['rate'],
        fx_date=income.date,
        recurrence_series_id=income.recurrence_series_id
    )
    db.add(new_income)
    db.commit()
    db.refresh(new_income)

    logger.info(f"User added new income {new_income.income_id}")
    return new_income


@router.patch('/{income_id}', response_model=IncomeResponse)
async def update_income(
    income_id: int,
    income_updates: IncomeUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
    fx_service: FXService = Depends(get_fx_service)
):

    income = db.query(Income).filter(
        Income.income_id == income_id
    ).first()

    if income is None:
        logger.warning("User is trying to update an nonexisting income")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "status": "NONEXISTENT_INCOME",
                "message": "User tried to update an income that does not exist"
            }
        )
    
    if income.user_id != user.user_id:
        logger.warning("User is not authorized to edit the income")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "status": "UNAUTHORIZED_INCOME_UPDATE",
                "message": "User not authorized to edit income"
            }
        )
    
    updated = False

    if (income_updates.new_date is not None):
        if income_updates.new_date > date.today():
            logger.warning("User tried to add future expense.")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "status": "FUTURE_EXPENSE_NOT_ALLOWED",
                    "message": "User is not allowed to add future expenses"
                }
            )
        income.date = income_updates.new_date
        updated = True
    
    if (income_updates.bulk is not None):
        income.bulk = income_updates.bulk
        if (income.date.day != 1) and (income.bulk):
            income.date = date(income.date.year, income.date.month, 1)
        updated = True

    if (income_updates.source is not None) and (income_updates.source != ""):
        income.source = income_updates.source
        updated = True
    
    amount_or_currency_change = False
    if (income_updates.currency is not None) and (income_updates.currency != ""):
        available_currencies = await fx_service.get_supported_codes()
        income_updates.currency = normalize_string(income_updates.currency)
        if income_updates.currency not in available_currencies:
            logger.warning("User tried to add an expense with an unsupported currency")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "status": "UNSUPPORTED_CURRENCY",
                    "message": "User tried to add an expense with an unsupported currency"
                }
            )
        income.currency = income_updates.currency
        amount_or_currency_change = True
        updated = True
    
    if (income_updates.original_amount is not None):
        income.original_amount = income_updates.original_amount
        amount_or_currency_change = True
        updated = True
    
    if amount_or_currency_change:
        converted_amount_and_rate = await fx_service.convert(db, income.currency, "USD", income.original_amount, income.date)
        income.usd_amount = converted_amount_and_rate['amount']
        income.fx_rate_to_usd = converted_amount_and_rate['rate']
        income.fx_date = income.date
    

    if updated:
        db.commit()
        db.refresh(income)
        logger.info(f"User updated income {income_id}")
    
    return income


@router.delete("/{income_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_income(
    income_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):

    income = db.query(Income).filter(
        Income.income_id == income_id
    ).first()

    if income is None:
        logger.warning("User is trying to delete an nonexisting income")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "status": "NONEXISTENT_INCOME",
                "message": "User tried to delete an income that does not exist"
            }
        )
    
    if income.user_id != user.user_id:
        logger.warning("User is not authorized to delete the income")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "status": "UNAUTHORIZED_INCOME_DELETE",
                "message": "User not authorized to delete income"
            }
        )
    
    db.delete(income)
    db.commit()
    logger.info(f"User delete income {income_id} request is successful")
    return Response(status_code=status.HTTP_204_NO_CONTENT)