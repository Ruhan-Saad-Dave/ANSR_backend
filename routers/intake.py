from fastapi import APIRouter, HTTPException
from pydantic import BaseModel  # Assuming TransactionData is a Pydantic model
from datetime import datetime

# Import the parsing function
from services.parsing_engine import parse_transaction

# Import the Supabase DB client
try:
    from core.setup import initialize_firebase

    db = initialize_firebase()
except ImportError:
    print("Error: Could not import 'initialize_firebase' from 'core.setup'.")
    db = None
except Exception as e:
    print(f"Error initializing database: {e}")
    db = None


# --- Define the Pydantic model (as referenced in your code) ---
class TransactionData(BaseModel):
    user_id: int
    timestamp: str  # e.g., "2025-11-13T14:30:00+05:30"
    raw_message: str
    # application_name: str # Add back if needed


router = APIRouter()


@router.post("/process", tags=["Intake"])
async def process_raw_transaction(data: TransactionData):
    """
    Receives raw transaction data, calls the parsing service,
    and saves the formatted data to the Supabase database.
    """
    if not db:
        raise HTTPException(status_code=500, detail="Database client is not initialized")

    # 1. Parse the raw message using the parsing service
    parsed_details = parse_transaction(data.raw_message)

    if not parsed_details:
        raise HTTPException(status_code=400, detail="Failed to parse transaction from raw_message")

    # 2. Format the data for Supabase
    try:
        dt_object = datetime.fromisoformat(data.timestamp)
    except (ValueError, TypeError):
        raise HTTPException(status_code=400, detail=f"Invalid timestamp format: {data.timestamp}")

    # Assemble the final dictionary to match your 'transaction' table schema
    final_data = {
        "user_id": data.user_id,
        "created_at": data.timestamp,  # Use the full ISO string
        "day": dt_object.strftime("%A"),  # e.g., "Monday"
        "amount": parsed_details.get("amount"),
        "sender_name": parsed_details.get("sender_name"),
        "payment_method": parsed_details.get("payment_method"),
        "payment_type": parsed_details.get("payment_type"),
        "category": parsed_details.get("category"),
        "message": parsed_details.get("message"),  # This comes from parse_transaction
        "anomaly": False  # Set a default value
    }

    # 3. Insert into Supabase 'transaction' table
    try:
        response = db.table('transaction').insert(final_data).execute()

        if not response.data:
            # This might happen if RLS fails, but .insert() usually errors
            raise Exception("No data returned from Supabase after insert.")

        print(f"✅ DB Write: Successfully wrote transaction for UserID '{data.user_id}'.")

        # Return the newly created transaction record from the DB
        return response.data[0]

    except Exception as e:
        print(f"❌ DB Write Error: {e}")
        # This will catch RLS (Row Level Security) policy violations
        raise HTTPException(status_code=500, detail=f"Data parsed but failed to save to database: {str(e)}")


@router.get("/test", tags=["Intake"])
async def test_endpoint():
    return {"message": "Intake endpoint is working"}