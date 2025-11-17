from fastapi import APIRouter, HTTPException
from pydantic import BaseModel  # Assuming TransactionData is a Pydantic model
from datetime import datetime

# --- Define the Pydantic model (as referenced in your code) ---
class TransactionData(BaseModel):
    user_id: str
    timestamp: str  # e.g., "2025-11-13T14:30:00+05:30"
    raw_message: str
    #application_name: str # Add back if needed

router = APIRouter()

@router.post("/test", tags=["test"])
async def process_raw_transaction(data: TransactionData):
    """
    Receives raw transaction data, calls the parsing service,
    and saves the formatted data to the Supabase database.
    """
    # Just return the received data for testing purposes
    return {"received_data": data.dict()}