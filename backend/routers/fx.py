from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from dependencies import get_current_user, get_db, get_fx_service
from models.core.user import User
from schemas.core.fx import FXRate, SupportedCodes, ConversionResponse
from services.fx_service import FXService
from decimal import Decimal
from utils.logger import logger

router = APIRouter(prefix='/fx', tags=['FX'])

@router.get('/exchange-rate', response_model=FXRate)
async def get_rate(
    from_currency: str = Query(..., examples="USD"),
    to_currency: str = Query(..., examples="AED"),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
    fx_service: FXService = Depends(get_fx_service)
):

    rate = await fx_service.get_latest_rate(db, from_currency, to_currency)

    logger.info(f"Returning exchange rate for {from_currency}-{to_currency}")
    return FXRate(rate=rate)


@router.get('/convert-amount', response_model=ConversionResponse)
async def get_conversion(
    from_currency: str = Query(..., examples="USD"),
    to_currency: str = Query(..., examples="AED"),
    amount: Decimal = Query(...),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
    fx_service: FXService = Depends(get_fx_service)
):

    data = await fx_service.convert(db, from_currency, to_currency, amount)

    logger.info(f"Returning converted amount and rate for {from_currency}-{to_currency}")
    return ConversionResponse(rate=data['rate'], amount=data['amount'])


@router.get('/codes', response_model=SupportedCodes)
async def get_codes(
    db: Session = Depends(get_db),
    fx_service: FXService = Depends(get_fx_service)
):

    codes = await fx_service.get_supported_codes()

    logger.info("Getting supported codes for exchange")
    return SupportedCodes(codes=codes)

