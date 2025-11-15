from pydantic import BaseModel
from typing import Optional

class TransactionReadOne(BaseModel):
    user_id: Optional[str] = None
    transaction_id: Optional[str] = None

class LimitReadOne(BaseModel):
    user_id: Optional[str] = None

class PendingReadOne(BaseModel):
    user_id: Optional[str] = None
    pending_id: Optional[str] = None

class SummaryReadOne(BaseModel):
    user_id: Optional[str] = None

class ChatHistoryReadOne(BaseModel):
    user_id: Optional[str] = None