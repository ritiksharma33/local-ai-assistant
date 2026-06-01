from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Float, DateTime, Text
from app.db.database import Base

class InferenceTelemetry(Base):
    __tablename__ = "inference_telemetry"

    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    endpoint_type = Column(String(50), nullable=False) # e.g., 'standard', 'structured', 'agent'
    model_used = Column(String(100), nullable=False)
    prompt_length = Column(Integer, nullable=False)
    tokens_per_second = Column(Float, default=0.0)
    total_time_seconds = Column(Float, default=0.0)
    execution_status = Column(String(50), default="SUCCESS") # SUCCESS or FAILED