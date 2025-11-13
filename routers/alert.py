import os
import json
from fastapi import APIRouter 

from models.alert import Alert
from core.setup import initialize_supabase

alert_router = APIRouter()
DB = initialize_supabase()

@alert_router.post("/set_daily_alert", tags = ["alert"])
async def set_daily_alert(alert: Alert):
    id = alert.id
    limit = alert.limit
    response = (
    DB.table("limit")
        .select("*")
        .eq("user_id", id)
        .execute()
    )
    if(len(response.data) > 0):
        DB.table("limit").update({"daily": limit}).eq("id", id).execute()
        return {"message": "Daily alert set successfully."}
    return {"message": "User ID does not exist"}

@alert_router.post("/set_weekly_alert", tags = ["alert"])
async def set_weekly_alert(alert: Alert):
    id = alert.id
    limit = alert.limit
    response = (
    DB.table("limit")
        .select("*")
        .eq("user_id", id)
        .execute()
    )
    if(len(response.data) > 0):
        DB.table("limit").update({"weekly": limit}).eq("id", id).execute()
        return {"message": "Weekly alert set successfully."}
    return {"message": "User ID does not exist"}

@alert_router.post("/set_monthly_alert", tags = ["alert"])
async def set_monthly_alert(alert: Alert):
    id = alert.id
    limit = alert.limit
    response = (
    DB.table("limit")
        .select("*")
        .eq("user_id", id)
        .execute()
    )
    if(len(response.data) > 0):
        DB.table("limit").update({"monthly": limit}).eq("id", id).execute()
        return {"message": "Monthly alert set successfully."}
    return {"message": "User ID does not exist"}

@alert_router.post("/set_yearly_alert", tags = ["alert"])
async def set_yearly_alert(alert: Alert):
    id = alert.id
    limit = alert.limit
    response = (
    DB.table("limit")
        .select("*")
        .eq("user_id", id)
        .execute()
    )
    if(len(response.data) > 0):
        DB.table("limit").update({"yearly": limit}).eq("id", id).execute()
        return {"message": "Yearly alert set successfully."}
    return {"message": "User ID does not exist"}