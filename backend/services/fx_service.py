import httpx
from sqlalchemy.orm import Session
from models.core.fx_rate import FXRate
from decimal import Decimal
from datetime import date
from utils.logger import logger
from utils.helpers import convert_unix_to_date
from typing import List
from dotenv import load_dotenv
import os

load_dotenv()
FX_API_BASE_URL = os.getenv("FX_API_BASE_URL", "https://v6.exchangerate-api.com/v6")
FX_API_KEY = os.getenv("FX_API_KEY")

class FXService():
    def __init__(self):
        self.client = httpx.AsyncClient(timeout=10.0)
        logger.info("Connecting to httpx async client")
    
    async def get_latest_rate(
        self,
        db: Session,
        from_currency: str,
        to_currency: str
    ) -> Decimal:
        """
        Get latest exchange rate for given currency

        Args:
        - from_currency: the base currency to convert from
        - to_currency: the currency to convert to

        Returns:
        - exchange rate value
        """

        # check if exchange rate for the day is already cached
        exists = db.query(FXRate).filter(
            FXRate.original_currency == from_currency.upper(),
            FXRate.to_currency == to_currency.upper(),
            FXRate.rate_date == date.today()
        ).first()

        if exists:
            logger.info("FX Rate already exists")
            return exists.rate
        
        url = f"{FX_API_BASE_URL}/{FX_API_KEY}/pair/{from_currency.upper()}/{to_currency.upper()}"

        response = await self.client.get(url)
        response.raise_for_status()
        data = response.json()

        if data["result"] != "success":
            error_type = data.get("error-type", "unknown-error")
            raise ValueError(f"ExchangeRate API error: {error_type}")

        rate_date = convert_unix_to_date(data["time_last_update_unix"])
        rate = Decimal(str(data["conversion_rate"]))

        new_rate = FXRate(
            original_currency=from_currency.upper(),
            to_currency=to_currency.upper(),
            rate=rate,
            rate_date=rate_date
        )
        db.add(new_rate)
        db.commit()
        db.refresh(new_rate)

        logger.info("Fetched rate successfully")
        return rate
    
    
    async def convert(
        self,
        db: Session,
        from_currency: str,
        to_currency: str,
        amount: Decimal,
    ) -> dict:
        """
        Converts given amount in from_currency to to_currency

        Args:
        - from_currency: the base currency to convert from
        - to_currency: the currency to convert to
        - amount: amount to convert

        Return:
        - {'rate': decimal, 'amount': decimal}
        """

        rate = await self.get_latest_rate(db, from_currency, to_currency)
        converted_amount = amount*rate

        logger.info("Fetched rate and converted successfully")
        return {
            'rate': rate,
            'amount': converted_amount
        }


    async def get_supported_codes(self) -> list[list[str]]:
        """
        Returns a list of lists of supported currency codes as
        [
            ["AED","UAE Dirham"],
            ["AFN","Afghan Afghani"],
            etc
        ]
        """

        url = f"{FX_API_BASE_URL}/{FX_API_KEY}/codes"
        response = await self.client.get(url)
        response.raise_for_status()

        data = response.json()
        if data["result"] != "success":
            error_type = data.get("error-type", "unknown-error")
            raise ValueError(f"ExchangeRate API error: {error_type}")
        

        return data["supported_codes"]


fx_service = FXService()