from pydantic import BaseModel
from typing import Optional, Dict, Any

class TransactionData(BaseModel):
    user_id: str
    timestamp: str  # e.g., "2025-11-13T14:30:00+05:30"
    raw_message: str
    # application_name: str # Add back if needed
    
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