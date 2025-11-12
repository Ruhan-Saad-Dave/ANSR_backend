from pydantic import BaseModel
from typing import Optional, Dict, Any

class TransactionData(BaseModel):
    user_id: str
    timestamp: str
    application_name: str
    sender_name: Optional[str] = None
    raw_message: str

class Timestamp(BaseModel):
    year: Optional[int]
    month: Optional[int]
    day: Optional[int]
    hour: Optional[int]

class CleanedData(BaseModel):
    ID: str
    timestamp: Timestamp
    sender: str
    payment_method: str
    payment_type: str
    Amount: Optional[float]
    Category: Optional[str]
    message: str

class ProcessResponse(BaseModel):
    cleaned_data: CleanedData
    alert_message: str
    anomaly_message: str
    firebase_status: str