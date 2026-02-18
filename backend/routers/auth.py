from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from dependencies import get_db, get_current_user
from models.core.user import User
from schemas.core.user import UserCreate, UserResponse, UserLogin, TokenWithUserResponse, UserPasswordChange, UserEmailChange
from schemas.core.token import OTPVerifyRequest, ResendOTPRequest
from utils.helpers import normalize_string
from utils.logger import logger
from utils.security import hash_password, generate_otp, hash_otp, send_otp, verify_password, create_access_token, verify_otp
from datetime import datetime, timedelta, timezone

router = APIRouter(prefix='/auth', tags=['Auth'])


@router.post('/register', response_model=UserResponse)
def register(user: UserCreate, db: Session = Depends(get_db)):
    email = normalize_string(user.email)
    name = user.name

    user_exists = db.query(User).filter(User.email == email).first()
    if user_exists and not user_exists.is_verified:
        logger.warning("User email already registered but is not verified")

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
    hashed_otp = hash_otp(otp, email)
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

    send_otp(email, name, otp)

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

    logger.info(f"User {user.user_id} logged in successfully")
    return TokenWithUserResponse(access_token=token, user=user)


@router.post("/verify-email-otp", status_code=status.HTTP_200_OK)
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


@router.post('/resend-otp', status_code=status.HTTP_200_OK)
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
    hashed_otp = hash_otp(otp, email)
    expiration = datetime.now(timezone.utc) + timedelta(minutes=10)

    user.otp_code = hashed_otp
    user.otp_expiration = expiration
    db.commit()
    db.refresh(user)

    name = user.name

    send_otp(email, name, otp)

    logger.info("OTP resent to user")
    return {
        "status": "OTP_RESENT",
        "message": "OTP resent successfully."
    }


@router.patch('/change-password', status_code=status.HTTP_200_OK)
def change_password(
    password_info: UserPasswordChange, 
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    
    if not verify_password(password_info.old_password, user.password):
        logger.warning(f"User is trying to change their password, but entered wrong password")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "code": "WRONG_PASSWORD",
                "message": "Wrong old password is entered"
            }
        )
    
    if password_info.old_password == password_info.new_password:
        logger.warning(f"User is using the same password to change their password")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "code": "SAME_PASSWORD",
                "message": "Same password is entered"
            }
        )
    
    user.password = hash_password(password_info.new_password)
    db.commit()
    db.refresh(user)

    logger.info("User's {user.user_id} password changed successfully")
    return {
            "status": "PASSWORD_CHANGED",
            "message": "Password changed successfully."
        }



# TO BE MODIFIED LATER
# @router.patch('/change-email', status_code=status.HTTP_200_OK)
# def change_email(
#     email_info: UserEmailChange,
#     db: Session = Depends(get_db),
#     user: User = Depends(get_current_user)
# ):

#     if not verify_password(email_info.current_password, user.password):
#         logger.warning("Invalid credentials, unable to change email")
#         raise HTTPException(
#             status_code=status.HTTP_403_FORBIDDEN,
#             detail={
#                 "status": "INVALID_CREDENTIALS",
#                 "message": "Invalid credentials, can't change email"
#             }
#         )
    
#     new_email = normalize_string(email_info.new_email)
#     if new_email == user.email:
#         logger.warning(f"User is using the same email to change their email")
#         raise HTTPException(
#             status_code=status.HTTP_400_BAD_REQUEST,
#             detail={
#                 "code": "SAME_EMAIL",
#                 "message": "Same email is entered"
#             }
#         )
    
#     email_unique = db.query(User).filter(User.email == new_email).first()
#     if email_unique is not None:
#         logger.warning("Email already registered")
#         raise HTTPException(
#             status_code=status.HTTP_400_BAD_REQUEST,
#             detail={
#                 "status": "EMAIL_NOT_UNIQUE",
#                 "message": "Please use an email that has not been registered before"
#             }
#         )
    
#     user.email = new_email
#     user.is_verified = False

#     otp = generate_otp()
#     hashed_otp = hash_otp(otp, new_email)
#     expiration = datetime.now(timezone.utc) + timedelta(minutes=10)
#     user.otp_code = hashed_otp
#     user.otp_expiration = expiration

#     db.commit()
#     db.refresh(user)

#     logger.info(f"User {user.user_id}'s email successfully changed, pending verification")
#     return JSONResponse(
#             status_code=status.HTTP_202_ACCEPTED,
#             content={
#                 "code": "EMAIL_CHANGED",
#                 "message": "Email changed, please verify account.",
#             }
#         )
