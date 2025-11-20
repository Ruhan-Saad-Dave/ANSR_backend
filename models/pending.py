from pydantic import BaseModel

class NewPending(BaseModel):
    user_id: str
    pending_id: str
    amount: float
    other_user: str
    reason: str
    is_current_debtor: str
    created_at: str

class RemovePending(BaseModel):
    user_id: str
    pending_id: str

class AllPending(BaseModel):
    user_id: str

class OnePending(BaseModel):
    user_id: str
    other_user: str