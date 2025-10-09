from fastapi import APIRouter, HTTPException

# Import the processing function from your service
from services.parsing_engine import process_transaction
from models.intake import TransactionData

router = APIRouter()


@router.post("/process", tags=["Intake"])
async def process_raw_transaction(data: TransactionData):
    """
    Receives raw transaction data from the mobile app, processes it,
    and returns the analysis.
    """
    try:
        # The parsing engine expects a single comma-separated string.
        # We construct it from the incoming JSON data.
        # Format: "ID, timestamp, application, sender (optional), exact message"
        
        sender = data.sender_name if data.sender_name else ""
        
        raw_data_string = f"{data.user_id},{data.timestamp},{data.application_name},{sender},{data.raw_message}"
        
        # Call the processing function
        result = process_transaction(raw_data_string)
        
        if "error" in result:
            raise HTTPException(status_code=400, detail=result["error"])
            
        return result
    except Exception as e:
        # Generic error handler for any unexpected issues
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {str(e)}")

