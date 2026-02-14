from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from dependencies import get_db
from models.core.user import User
from schemas.core.user import UserCreate, UserResponse, UserLogin, TokenWithUserResponse
from schemas.core.token import OTPVerifyRequest, ResendOTPRequest
from utils.helpers import normalize_string
from utils.logger import logger
from utils.security import hash_password, generate_otp, hash_otp, send_otp, verify_password, create_access_token, verify_otp
from datetime import datetime, timedelta, timezone

router = APIRouter(prefix='/auth', tags=['Auth'])


@router.post('/register', response_model=UserResponse)
def register(user: UserCreate, db: Session = Depends(get_db)):
    email = normalize_string(user.email)
    name = normalize_string(user.name)

    user_exists = db.query(User).filter(User.email == email).first()
    if user_exists and not user_exists.is_verified:
        logger.warning("User email already registered but is not verified, OTP resent")

        return JSONResponse(
            status_code=status.HTTP_202_ACCEPTED,
            content={
                "code": "PENDING_VERIFICATION",
                "message": "Account already exists but is not verified.",
                "email": email
            }
        )
    
    if user_exists and user_exists.is_verified:
        logger.warning("User email is already registeted and is verified")
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "code": "EMAIL_ALREADY_VERIFIED",
                "message": "Email is already registered. Please login."
            }
        )


    password = hash_password(user.password)
    otp = generate_otp()
    hashed_otp = hash_otp(otp)
    expiration = datetime.now(timezone.utc) + timedelta(minutes=10)

    new_user = User(
        email=email,
        password=password,
        name=name,
        country=user.country,
        city=user.city,
        preferred_currency=user.preferred_currency,
        is_verified=False,
        otp_code=hashed_otp,
        otp_expiration=expiration
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    send_otp(email, otp)

    logger.info(f"New user registered and verification is pending")
    return new_user


@router.post('/login', response_model=TokenWithUserResponse)
def login(user_info: UserLogin, db: Session = Depends(get_db)):
    email = normalize_string(user_info.email)
    
    user = db.query(User).filter(User.email == email).first()
    if user is None or not verify_password(user_info.password, user.password):
        logger.warning("Invalid Credentials while trying to login!")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, 
            detail={
                "code": "INVALID_CREDENTIALS",
                "message": "Invalid email or password"
            }
        )
    
    if not user.is_verified:
        logger.warning("User is not verified and is trying to login")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "code": "EMAIL_NOT_VERIFIED",
                "message": "Please verify your email before logging in"
            }
        )
    
    token = create_access_token(data={"sub":str(user.user_id)})

    logger.info("User logged in successfully")
    return TokenWithUserResponse(access_token=token, user=user)


@router.post("/verify-email-otp")
def verify_email_otp(data: OTPVerifyRequest, db: Session = Depends(get_db)):
    email = normalize_string(data.email)
    user = db.query(User).filter(User.email == email).first()

    if user is None:
        logger.warning("User tried to verify email, but user does not exist")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail={
                "code": "USER_NOT_FOUND",
                "message": "User is not registered yet."
            }
        )

    if user.is_verified:
        logger.warning("User is already verified and is trying to verify again")
        return {
            "status": "EMAIL_ALREADY_VERIFIED",
            "message": "Email already verified."
        }

    if not user.otp_code:
        logger.warning("User does not have an existing OTP")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail={
                "code" : "NO_OTP",
                "message": "NO OTP found, please resend OTP"
            }
        )
    
    if user.otp_expiration < datetime.now(timezone.utc):
        logger.warning("User's OTP has expired")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail={
                "code" : "OTP_EXPIRED",
                "message": "OTP Expired, please resend OTP"
            }
        )

    if not verify_otp(data.otp, email, user.otp_code):
        logger.warning("Wrong OTP code is given during verification")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail={
                "code" : "INVALID_OTP",
                "message": "Incorrect OTP"
            }
        )
    
    user.is_verified = True
    user.otp_code = None
    user.otp_expiration = None
    db.commit()
    db.refresh(user)

    logger.info("User email verified successfully")
    return {
            "status": "EMAIL_VERIFIED",
            "message": "Email verified successfully. You can now login."
        }


@router.post('/resend-otp')
def resend_otp(data: ResendOTPRequest, db: Session = Depends(get_db)):
    email = normalize_string(data.email)
    user = db.query(User).filter(User.email == email).first()

    if user is None:
        logger.warning("User requested to resend otp, but is not registered")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail={
                "code" : "USER_NOT_FOUND",
                "message": "User is not registered yet."
            }
        )

    if user.is_verified:
        logger.warning("User is already verified and is trying to verify again")
        return {
            "status": "EMAIL_ALREADY_VERIFIED",
            "message": "Email already verified."
        }
    
    otp = generate_otp()
    hashed_otp = hash_otp(otp)
    expiration = datetime.now(timezone.utc) + timedelta(minutes=10)

    user.otp_code = hashed_otp
    user.otp_expiration = expiration
    db.commit()
    db.refresh(user)

    send_otp(email, otp)

    logger.info("OTP resent to user")
    return {
        "status": "OTP_RESENT",
        "message": "OTP resent successfully."
    }
