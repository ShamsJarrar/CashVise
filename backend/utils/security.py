from passlib.context import CryptContext
from jose import jwt, JWTError
from datetime import datetime, timedelta, timezone
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
from dotenv import load_dotenv
from .logger import logger
import secrets
import hmac, hashlib
import os


load_dotenv()
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM")
ACCESS_TOKEN_EXPIRE_MINS = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINS", 30))
SENDGRID_API_KEY = os.getenv("SENDGRID_API_KEY")
SENDGRID_TEMPLATE_ID = os.getenv("SENDGRID_TEMPLATE_ID")
FROM_EMAIL = os.getenv("FROM_EMAIL")
OTP_SECRET_KEY = os.getenv("OTP_SECRET_KEY")


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    logger.debug("Hashing password")
    return pwd_context.hash(password)

def verify_password(entered_password: str, hashed_password: str) -> bool:
    logger.debug("Verifying password")
    return pwd_context.verify(entered_password, hashed_password)


def create_access_token(data: dict) -> str:
    logger.debug("Creating access token")

    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINS)
    to_encode.update({"exp" : expire})
    return jwt.encode(to_encode, JWT_SECRET_KEY, algorithm=ALGORITHM)

def decode_access_token(token: dict) -> str:
    logger.debug("Decoding access token")

    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[ALGORITHM])
        logger.debug("Token decoded successfully")
        return payload
    except JWTError as e:
        logger.error("Failed to decode token: %s", str(e))
        raise JWTError("Invalid token") from e


def generate_otp(length: int = 6) -> str:
    logger.debug("Generating otp")
    return f"{secrets.randbelow(10**length):0{length}d}"

def hash_otp(otp: str, email: str) -> str:
    logger.debug("Hashing otp")
    msg = f"{email}:{otp}".encode("utf-8")
    return hmac.new(OTP_SECRET_KEY.encode("utf-8"), msg, hashlib.sha256).hexdigest()

def verify_otp(given_otp: str, email: str, stored_otp_hash: str) -> bool:
    logger.debug("Verifying otp")
    given_otp_hash = hash_otp(given_otp, email)
    return hmac.compare_digest(given_otp_hash, stored_otp_hash)

def send_otp(email: str, name: str, otp: str):
    message = Mail(
        from_email=FROM_EMAIL,
        to_emails=email,
        subject="Your verification code"
    )
    message.template_id = SENDGRID_TEMPLATE_ID
    message.dynamic_template_data = {
        "name": name or "User",
        "otp": otp,
    }

    try:
        sg = SendGridAPIClient(SENDGRID_API_KEY)
        response = sg.send(message)
        logger.info(f"OTP sent to email: {email} - status {response.status_code}")
    except Exception as e:
        logger.error(f"Failed to send OTP email: {e}")
        raise 