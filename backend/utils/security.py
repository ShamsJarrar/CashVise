from passlib.context import CryptContext
from jose import jwt, JWTError
from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv
from .logger import logger
import os


load_dotenv()
SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM")
ACCESS_TOKEN_EXPIRE_MINS = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINS", 30))
SENDGRID_API_KEY = os.getenv("SENDGRID_API_KEY")
FROM_EMAIL = os.getenv("FROM_EMAIL")


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    logger.debug("Hashing password")
    return pwd_context.hash(password)

def verify_password(og_password: str, hashed_password: str) -> bool:
    logger.debug("Verifying password")
    return pwd_context.verify(og_password, hashed_password)


def create_access_token(data: dict) -> str:
    logger.debug("Creating access token")

    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINS)
    to_encode.update({"exp" : expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def decode_access_token(token: dict) -> str:
    logger.debug("Decoding access token")

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        logger.debug("Token decoded successfully")
        return payload
    except JWTError as e:
        logger.error("Failed to decode token: %s", str(e))
        raise JWTError("Invalid token") from e


