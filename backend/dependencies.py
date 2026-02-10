from database import SessionLocal
from sqlalchemy.orm import Session
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from models.core.user import User
from schemas.core.token import TokenPayload
from utils.security import decode_access_token
from jose import JWTError
from utils.logger import logger


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


def get_db():
    db: Session = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> User:
    logger.debug("Getting user")

    try:
        payload = decode_access_token(token)
        token_data = TokenPayload(**payload)
        logger.debug("Successfully decoded token")
    except (JWTError, ValueError):
        logger.error("Couldn't decode token, can't get user")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token, can't authorize access"
        )
    
    user = db.query(User).filter(User.user_id == int(token_data.sub)).first()
    if not user:
        logger.error("User does not exist, can't get user")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User does not exist"
        )
    return user
