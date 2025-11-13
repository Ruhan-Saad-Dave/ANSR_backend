from pydantic import BaseModel
from typing import Optional

class TransactionReadOne(BaseModel):
    user_id: Optional[int] = None
    transaction_id: Optional[int] = None

class LimitReadOne(BaseModel):
    user_id: Optional[int] = None

class PendingReadOne(BaseModel):
    user_id: Optional[int] = None
    pending_id: Optional[int] = None

class SummaryReadOne(BaseModel):
    user_id: Optional[int] = None

class ChatHistoryReadOne(BaseModel):
    user_id: Optional[int] = None