import os
import json
import firebase_admin
from firebase_admin import credentials, firestore
from fastapi import APIRouter 

from models.alert import Alert
from core.setup import initialize_firebase

alert_router = APIRouter()
DB = initialize_firebase()

@alert_router.post("/set_daily_alert", tags = ["alert"])
async def set_daily_alert(alert: Alert):
    id = alert.id
    limit = alert.limit
    doc_ref = DB.collection('Limit Table').document('LimTab')
    doc = doc_ref.get()
    doc_ref.update({
        "Weekly limit" : doc.to_dict().get("Weekly limit"),
        "Yearly limit" : doc.to_dict().get("Yearly limit"),
        "ID" : id, 
        "Daily Limit" : limit, 
        "Monthly limit" : doc.to_dict().get("Monthly limit")
    })
    return {"message": "daily alert set"}

@alert_router.post("/set_weekly_alert", tags = ["alert"])
async def set_weekly_alert(alert: Alert):
    id = alert.id
    limit = alert.limit
    doc_ref = DB.collection('Limit Table').document('LimTab')
    doc = doc_ref.get()
    doc_ref.update({
        "Weekly limit" : limit,
        "Yearly limit" : doc.to_dict().get("Yearly limit"),
        "ID" : id, 
        "Daily Limit" : doc.to_dict().get("Daily Limit"), 
        "Monthly limit" : doc.to_dict().get("Monthly limit")
    })
    return {"message": "weekly alert set"}

@alert_router.post("/set_monthly_alert", tags = ["alert"])
async def set_monthly_alert(alert: Alert):
    id = alert.id
    limit = alert.limit
    doc_ref = DB.collection('Limit Table').document('LimTab')
    doc = doc_ref.get()
    doc_ref.update({
        "Weekly limit" : doc.to_dict().get("Weekly limit"),
        "Yearly limit" : doc.to_dict().get("Yearly limit"),
        "ID" : id, 
        "Daily Limit" : doc.to_dict().get("Daily Limit"), 
        "Monthly limit" : limit
    })
    return {"message": "monthly alert set"}

@alert_router.post("/set_yearly_alert", tags = ["alert"])
async def set_yearly_alert(alert: Alert):
    id = alert.id
    limit = alert.limit
    doc_ref = DB.collection('Limit Table').document('LimTab')
    doc = doc_ref.get()
    doc_ref.update({
        "Weekly limit" : doc.to_dict().get("Weekly limit"),
        "Yearly limit" : limit,
        "ID" : id, 
        "Daily Limit" : doc.to_dict().get("Daily Limit"), 
        "Monthly limit" : doc.to_dict().get("Monthly limit")
    })
    return {"message": "yearly alert set"}