from fastapi import APIRouter, HTTPException 
from datetime import datetime

from models.pending import *
from core.setup import initialize_supabase
from services.pending import clean

router = APIRouter()
DB = initialize_supabase()

@router.post("/new_entry", tags = ["Pending Payment"])
def add_pending_payment(data: NewPending):
    """
    Adds a pending payment entry for a user.
    """
    user_id = data.user_id
    pending_id = data.pending_id
    amount = data.amount
    other_user = data.other_user
    reason = data.reason
    is_current_debtor = data.is_current_debtor
    created_at = data.created_at

    if created_at is None:
        created_at = datetime.now().isoformat()

    try:
        DB.table("pending").insert({
            "user_id": user_id,
            "pending_id": pending_id,
            "amount": int(amount),
            "other_user": other_user,
            "reason": reason,
            "is_current_debtor": is_current_debtor,
            "created_at": created_at
        }).execute()
        return {"Success": "Pending payment added."}
    except Exception as e:
        return HTTPException(status_code=500, detail=str(e))
    
@router.post("/remove_entry", tags = ["Pending Payment"])
def remove_pending_payment(data: RemovePending):
    """
    Removes a pending payment entry for a user.
    """
    user_id = data.user_id
    pending_id = data.pending_id

    try:
        DB.table("pending").delete().eq("user_id", user_id).eq("pending_id", pending_id).execute()
        return {"Success": "Pending payment removed."}
    except Exception as e:
        return HTTPException(status_code=500, detail=str(e))
    
@router.post("/get_all_pending", tags = ["Pending Payment"])
def get_pending_payments(data: AllPending):
    """
    Retrieves all pending payment entries for a user.
    """
    user_id = data.user_id
    try:
        response = DB.table("pending").select("*").eq("user_id", user_id).execute()
        cleaned_data = clean(response.data)
        returned_data = {"raw" : response.data, "cleaned" : cleaned_data}
        return returned_data
    except Exception as e:
        return HTTPException(status_code=500, detail=str(e))

@router.post("/get_pending_of", tags = ["Pending Payment"])
def get_pending_payments_of(data: OnePending):
    """
    Retrieves all pending payment entries of a specific other user to the current user.
    """
    user_id = data.user_id
    other_user = data.other_user
    try:
        response = (
            DB.table("pending")
            .select("*")
            .eq("user_id", user_id)
            .eq("other_user", other_user)
            .execute()
        )
        cleaned_data = clean(response.data)

        returned_data = {"raw" : response.data, "cleaned" : cleaned_data}
        return returned_data
    except Exception as e:
        return HTTPException(status_code=500, detail=str(e))