from pydantic import BaseModel, EmailStr


class TokenPayload(BaseModel):
    sub: str
    exp: int

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"

class OTPVerifyRequest(BaseModel):
    email: EmailStr
    otp: str

class ResendOTPRequest(BaseModel):
    email: EmailStr