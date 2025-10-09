from fastapi import APIRouter, HTTPException
from services.recurring_detector import detect_recurring

router = APIRouter(tags=["Recurring Payments"])

@router.get("/{user_id}")
def get_user_recurrings(user_id: str):
    """
    Detects and returns a list of potential recurring payment for a given user.
    """
    try:
        recurrings = detect_recurring(user_id)
        if not recurrings:
            return {"message": "No recurring payments detected."}
        return recurrings
    except Exception as e:
        # For any unexpected errors in the detection logic
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")
