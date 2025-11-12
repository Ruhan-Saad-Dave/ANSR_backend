from fastapi import APIRouter, HTTPException
from models.intake import TransactionData

# Import the main formatting function and the DB instance
from services.parsing_engine import format_transaction_data

from core.setup import db
router = APIRouter()

def add_transaction_to_db(db, formatted_transaction, user_id):
    if not db:
        return False
    try:
        payment_type = formatted_transaction.get("payment_type")
        if payment_type == 'income':
            collection_name = 'Income'
        elif payment_type == 'expense':
            collection_name = 'Expenses'
        else:
            print(f"❌ DB Write Error: Unknown payment_type '{payment_type}'")
            return False

        user_doc_ref = db.collection(collection_name).document(user_id)
        user_doc_ref.collection('transactions').add(formatted_transaction)
        print(f"✅ DB Write: Successfully wrote transaction for UserID '{user_id}'.")
        return True
    except Exception as e:
        print(f"❌ DB Write Error: {e}")
        return False


@router.post("/process", tags=["Intake"])
async def process_raw_transaction(data: TransactionData):
    """
    Receives raw transaction data, parses it, formats it,
    and saves it to the database.
    """
    try:
        # Call the formatting function with the correct arguments
        formatted_data = format_transaction_data(
            timestamp_str=data.timestamp,
            app_name=data.application_name,
            raw_message=data.raw_message
        )

        if not formatted_data:
            raise HTTPException(status_code=400, detail="Failed to parse transaction from raw_message")

        # Add the user_id to the data that will be saved
        db_data = formatted_data.copy()
        db_data['user_id'] = data.user_id

        # Save the transaction to the database
        db_success = add_transaction_to_db(db, db_data, data.user_id)

        if not db_success:
            raise HTTPException(status_code=500, detail="Data parsed but failed to save to database")

        return formatted_data
    except HTTPException as e:
        # Re-raise HTTPException to let FastAPI handle it
        raise e
    except Exception as e:
        # Generic error handler for any unexpected issues
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {str(e)}")


@router.get("/test", tags=["Intake"])
async def test_endpoint():
    return {"message": "Intake endpoint is working"}