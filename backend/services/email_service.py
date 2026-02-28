from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
from dotenv import load_dotenv
from utils.logger import logger
import os

load_dotenv()
SENDGRID_API_KEY = os.getenv("SENDGRID_API_KEY")
SENDGRID_TEMPLATE_ID = os.getenv("SENDGRID_TEMPLATE_ID")
FROM_EMAIL = os.getenv("FROM_EMAIL")

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