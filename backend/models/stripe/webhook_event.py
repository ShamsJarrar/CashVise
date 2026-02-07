from sqlalchemy import Column, Integer, String, DateTime, func, Text, BigInteger, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import JSONB
from database import Base
import enum

class WebhookStatus(str, enum.Enum):
    RECEIVED = "RECEIVED"
    PROCESSING = "PROCESSING"
    PROCESSED = "PROCESSED"
    FAILED = "FAILED"

class WebhookEvent(Base):
    __tablename__ = "webhook_events"

    id = Column(Integer, primary_key=True, index=True)
    stripe_event_id = Column(String(255), unique=True, nullable=False)
    type = Column(String(255), nullable=False, index=True)
    stripe_created_ts = Column(BigInteger, nullable=False)
    received_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    payload = Column(JSONB, nullable=False)
    status = Column(Enum(WebhookStatus, name="webhook_status"), nullable=False, server_default="RECEIVED")
    processed_at = Column(DateTime(timezone=True), nullable=True)
    error = Column(Text, nullable=True)

