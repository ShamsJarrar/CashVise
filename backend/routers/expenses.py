from fastapi import APIRouter, Depends, HTTPException, status, Query, Response
from sqlalchemy.orm import Session
from dependencies import get_db, get_current_user, get_fx_service
from models.core.user import User
from models.core.expense import Expense
from schemas.core.expense import ExpenseCreate, ExpenseResponse, ExpenseUpdate
from services.fx_service import FXService
from utils.helpers import normalize_string
from utils.logger import logger
from typing import List, Optional
from datetime import date

router = APIRouter(prefix='/expenses', tags=['Expenses'])

@router.get('/', response_model=List[ExpenseResponse])
def get_expenses(
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):

    date_filters = []
    if start_date is not None:
        date_filters.append(Expense.date >= start_date)
    
    if end_date is not None:
        date_filters.append(Expense.date <= end_date)

    expenses = db.query(Expense).filter(
        Expense.user_id == user.user_id,
        *date_filters
    ).all()

    return expenses


@router.get('/{expense_id}', response_model=ExpenseResponse)
def get_expense(
    expense_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):

    expense = db.query(Expense).filter(
        Expense.expense_id == expense_id
    ).first()

    if expense is None:
        logger.warning("User tried to fetch expense using expense_id, but expenses does not exist")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "status": "EXPENSE_NOT_FOUND",
                "message": "Expense you tried to fetch does not exist"
            }
        )
    
    if expense.user_id != user.user_id:
        logger.warning("User is not authorized to access the expense they tried to fetch")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "status": "FORBIDDEN_ACCESS_TO_EXPENSE",
                "message": "User is not authorized to access the expense"
            }
        )
    
    return expense


@router.post('/', response_model=ExpenseResponse)
async def add_expense(
    expense: ExpenseCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
    fx_service: FXService = Depends(get_fx_service)
):

    if expense.date > date.today():
        logger.warning("User tried to add future expense.")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "status": "FUTURE_EXPENSE_NOT_ALLOWED",
                "message": "User is not allowed to add future expenses"
            }
        )
    
    if expense.currency is None:
        expense.currency = user.preferred_currency
    
    available_currencies = await fx_service.get_supported_codes()
    expense.currency = normalize_string(expense.currency)
    if expense.currency not in available_currencies:
        logger.warning("User tried to add an expense with an unsupported currency")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "status": "UNSUPPORTED_CURRENCY",
                "message": "User tried to add an expense with an unsupported currency"
            }
        )
    
    # force bulk expenses to be on the first day of the month if frontend didn't do it
    if expense.bulk == True:
        if expense.date.day != 1:
            expense.date = date(expense.date.year, expense.date.month, 1)
    
    converted_amount_and_rate = await fx_service.convert(db, expense.currency, "USD", expense.original_amount, expense.date)

    new_expense = Expense(
        user_id=user.user_id,
        date=expense.date,
        bulk=expense.bulk,
        expense_category=expense.expense_category,
        currency=expense.currency,
        original_amount=expense.original_amount,
        usd_amount=converted_amount_and_rate['amount'],
        fx_rate_to_usd=converted_amount_and_rate['rate'],
        fx_date=expense.date,
        recurrence_series_id=expense.recurrence_series_id,
    )
    db.add(new_expense)
    db.commit()
    db.refresh(new_expense)

    logger.info(f"User added new expense {new_expense.expense_id}")
    return new_expense


@router.patch('/{expense_id}', response_model=ExpenseResponse)
async def update_expense(
    expense_id: int,
    expense_updates: ExpenseUpdate, 
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
    fx_service: FXService = Depends(get_fx_service)
):

    expense = db.query(Expense).filter(
        Expense.expense_id == expense_id
    ).first()

    if expense is None:
        logger.warning("User is trying to update an nonexisting expense")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "status": "NONEXISTENT_EXPENSE",
                "message": "User tried to update an expense that does not exist"
            }
        )
    
    if expense.user_id != user.user_id:
        logger.warning("User is not authorized to edit the expense")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "status": "UNAUTHORIZED_EXPENSE_UPDATE",
                "message": "User not authorized to edit expense"
            }
        )
    
    updated = False

    if (expense_updates.new_date is not None):
        if expense_updates.new_date > date.today():
            logger.warning("User tried to add future expense.")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "status": "FUTURE_EXPENSE_NOT_ALLOWED",
                    "message": "User is not allowed to add future expenses"
                }
            )
        expense.date = expense_updates.new_date
        updated = True
    
    if (expense_updates.bulk is not None):
        expense.bulk = expense_updates.bulk
        if (expense.date.day != 1) and (expense.bulk):
            expense.date = date(expense.date.year, expense.date.month, 1)
        updated = True
    
    if (expense_updates.expense_category is not None) and (expense_updates.expense_category != ""):
        expense.expense_category = expense_updates.expense_category
        updated = True
    
    amount_or_currency_change = False
    if (expense_updates.currency is not None) and (expense_updates.currency != ""):
        available_currencies = await fx_service.get_supported_codes()
        expense_updates.currency = normalize_string(expense_updates.currency)
        if expense_updates.currency not in available_currencies:
            logger.warning("User tried to add an expense with an unsupported currency")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "status": "UNSUPPORTED_CURRENCY",
                    "message": "User tried to add an expense with an unsupported currency"
                }
            )
        expense.currency = expense_updates.currency
        amount_or_currency_change = True
        updated = True
    
    if (expense_updates.original_amount is not None):
        expense.original_amount = expense_updates.original_amount
        amount_or_currency_change = True
        updated = True

    if amount_or_currency_change:
        converted_amount_and_rate = await fx_service.convert(db, expense.currency, "USD", expense.original_amount, expense.date)
        expense.usd_amount = converted_amount_and_rate['amount']
        expense.fx_rate_to_usd = converted_amount_and_rate['rate']
        expense.fx_date = expense.date


    if updated:
        db.commit()
        db.refresh(expense)
        logger.info(f"User updated expense {expense_id}")
    
    return expense


@router.delete("/{expense_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_expense(
    expense_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):

    expense = db.query(Expense).filter(
        Expense.expense_id == expense_id
    ).first()

    if expense is None:
        logger.warning("User is trying to delete an nonexisting expense")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "status": "NONEXISTENT_EXPENSE",
                "message": "User tried to delete an expense that does not exist"
            }
        )

    if expense.user_id != user.user_id:
        logger.warning("User is not authorized to delete the expense")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "status": "UNAUTHORIZED_EXPENSE_DELETE",
                "message": "User not authorized to delete expense"
            }
        )
    
    db.delete(expense)
    db.commit()
    logger.info(f"User delete expense {expense_id} request is successful")
    return Response(status_code=status.HTTP_204_NO_CONTENT)