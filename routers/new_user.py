from fastapi import APIRouter, HTTPException

from models.new_user import NewUser
from core.setup import initialize_supabase

router = APIRouter()
DB = initialize_supabase()

@router.post("/", tags = ["New User Setup"])
def new_user_setup(data: NewUser):
    """
    Initializes database entries for a new user.
    """
    user_id = data.user_id
    try:
        DB.table("limit").insert({
            "user_id": user_id,
            "daily" : -1,
            "weekly" : -1,
            "monthly" : -1,
            "yearly" : -1
        }).execute()

        DB.table("summary").insert({
            "user_id" : user_id, 
            "day_income" : 0,
            "week_income" : 0,
            "month_income" : 0,
            "year_income" : 0,
            "day_expense" : 0,
            "week_expense" : 0,
            "month_expense" : 0,
            "year_expense" : 0,
            "day_cashflow" : 0,
            "week_cashflow" : 0,
            "month_cashflow" : 0,
            "year_cashflow" : 0
        }).execute()

        DB.table("chat_history").insert({
            "user_id" : user_id,
            "chat_history" : []
        }).execute()
        return {"Success": "User setup completed."}
    except Exception as e:
        return HTTPException(status_code=500, detail=str(e))
