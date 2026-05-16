import httpx
from sqlalchemy.orm import Session
from models.core.fx_rate import FXRate
from decimal import Decimal
from datetime import date, datetime, timedelta, timezone
from utils.logger import logger
from utils.helpers import normalize_string
from dotenv import load_dotenv
import os

load_dotenv()
FX_API_BASE_URL = os.getenv("FX_API_BASE_URL")
FALLBACK_URL = os.getenv("FALLBACK_URL")

class FXService():
    def __init__(self):
        self.client = httpx.AsyncClient(timeout=10.0)
        self._supported_codes_cache = None
        self._supported_codes_cache_expiry = None
        logger.info("Connecting to httpx async client")
    
    async def get_rate(
        self,
        db: Session,
        from_currency: str,
        to_currency: str,
        date_of_rate: date
    ) -> Decimal:
        """
        Get exchange rate for given currency and date

        Args:
        - from_currency: the base currency to convert from
        - to_currency: the currency to convert to
        - date_of_rate: date to get rate for

        Returns:
        - exchange rate value
        """

        from_currency = normalize_string(from_currency)
        to_currency = normalize_string(to_currency)

        # check if exchange rate for the day is already cached
        exists = db.query(FXRate).filter(
            FXRate.original_currency == from_currency,
            FXRate.to_currency == to_currency,
            FXRate.rate_date == date_of_rate
        ).first()

        if exists:
            logger.info("FX Rate already exists")
            return exists.rate

        urls = []
        if date_of_rate == date.today():
            urls.append(f"{FX_API_BASE_URL}@latest/v1/currencies/{from_currency}.json")
            urls.append(f"https://latest.{FALLBACK_URL}/{from_currency}.json")
        else:
            urls.append(f"{FX_API_BASE_URL}@{date_of_rate}/v1/currencies/{from_currency}.json")
            urls.append(f"https://{date_of_rate}.{FALLBACK_URL}/{from_currency}.json")

        for url in urls:
            try:
                logger.info(f"Fetching {url}")
                response = await self.client.get(url)
                response.raise_for_status()
                data = response.json()

                rate = Decimal(str(data[f"{from_currency}"][f"{to_currency}"]))

                new_rate = FXRate(
                    original_currency=from_currency,
                    to_currency=to_currency,
                    rate=rate,
                    rate_date=date_of_rate
                )
                db.add(new_rate)
                db.commit()
                db.refresh(new_rate)

                logger.info("Fetched rate successfully")
                return rate
            except httpx.HTTPError as e:
                logger.warning(f"Failed to fetch {url}")
    
    
    async def convert(
        self,
        db: Session,
        from_currency: str,
        to_currency: str,
        amount: Decimal,
        date_of_rate: date
    ) -> dict:
        """
        Converts given amount in from_currency to to_currency

        Args:
        - from_currency: the base currency to convert from
        - to_currency: the currency to convert to
        - amount: amount to convert
        - date_of_rate: date to get rate for

        Return:
        - {'rate': decimal, 'amount': decimal}
        """

        rate = await self.get_rate(db, from_currency, to_currency, date_of_rate)
        converted_amount = amount*rate

        logger.info("Fetched rate and converted successfully")
        return {
            'rate': rate,
            'amount': converted_amount
        }


    async def get_supported_codes(self) -> dict:
        """
        Returns a dictionary supported currency codes as
        {
            "1inch": "1inch",
            "aave": "Aave",
            "ada": "Cardano",
            "aed": "Emirati Dirham",
            ...
        }

        Returns cached results if not expired yet to avoid
        connection error
        """
        
        now = datetime.now(timezone.utc)
        if  (self._supported_codes_cache is not None) and \
            (self._supported_codes_cache_expiry is not None) and \
            (now < self._supported_codes_cache_expiry):
            logger.info("Returning cached codes")
            return self._supported_codes_cache


        url = f"{FX_API_BASE_URL}@latest/v1/currencies.json"
        response = await self.client.get(url)
        response.raise_for_status()

        data = response.json()

        self._supported_codes_cache = data
        self._supported_codes_cache_expiry = now + timedelta(hours=24)

        logger.info("Fetched codes successfully")
        return data


fx_service = FXService()