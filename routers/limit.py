from fastapi import APIRouter 

from models.limit import Limit
from core.setup import initialize_supabase

router = APIRouter()
DB = initialize_supabase()

@router.post("/set_spending_limit", tags = ["Spending Limit"])
def set_spending_limit(data: Limit):
    """
    Sets spending limits for a user.
    Availabile limit types: daily, weekly, monthly, yearly.
    """
    user_id = data.user_id
    limit_type = data.limit_type
    if limit_type.lower() not in ["daily", "weekly", "monthly", "yearly"]:
        return {"Error": "Invalid limit type. Choose from 'daily', 'weekly', 'monthly', 'yearly'."}
    limit = data.limit

    response = (
    DB.table("limit")
        .select("*")
        .eq("user_id", user_id)
        .execute()
    )
    if(len(response.data) > 0):
        DB.table("limit").update({limit_type: limit}).eq("user_id", id).execute()
        return {"Success": f"{limit_type} alert set successfully."}
    return {"Error": "User ID does not exist"}

# todo: get spending limit