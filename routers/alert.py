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
    doc_ref = DB.collection('Limit Table').document(id)
    doc = doc_ref.get()

    if doc.exists:
        # Document exists, just update the daily limit
        doc_ref.update({
            "Daily Limit": limit
        })
    else:
        # Document does not exist, create it with default structure
        doc_ref.set({
            "Daily Limit": limit,
            "Weekly limit": 0,
            "Monthly limit": 0,
            "Yearly limit": 0
        })
    return {"message": "daily alert set"}

@alert_router.post("/set_weekly_alert", tags = ["alert"])
async def set_weekly_alert(alert: Alert):
    id = alert.id
    limit = alert.limit
    doc_ref = DB.collection('Limit Table').document(id)
    doc = doc_ref.get()

    if doc.exists:
        # Document exists, just update the weekly limit
        doc_ref.update({
            "Weekly limit": limit
        })
    else:
        # Document does not exist, create it with default structure
        doc_ref.set({
            "Daily Limit": 0,
            "Weekly limit": limit,
            "Monthly limit": 0,
            "Yearly limit": 0
        })
    return {"message": "weekly alert set"}

@alert_router.post("/set_monthly_alert", tags = ["alert"])
async def set_monthly_alert(alert: Alert):
    id = alert.id
    limit = alert.limit
    doc_ref = DB.collection('Limit Table').document(id)
    doc = doc_ref.get()

    if doc.exists:
        # Document exists, just update the monthly limit
        doc_ref.update({
            "Monthly limit": limit
        })
    else:
        # Document does not exist, create it with default structure
        doc_ref.set({
            "Daily Limit": 0,
            "Weekly limit": 0,
            "Monthly limit": limit,
            "Yearly limit": 0
        })
    return {"message": "monthly alert set"}

@alert_router.post("/set_yearly_alert", tags = ["alert"])
async def set_yearly_alert(alert: Alert):
    id = alert.id
    limit = alert.limit
    doc_ref = DB.collection('Limit Table').document(id)
    doc = doc_ref.get()

    if doc.exists:
        # Document exists, just update the yearly limit
        doc_ref.update({
            "Yearly limit": limit
        })
    else:
        # Document does not exist, create it with default structure
        doc_ref.set({
            "Daily Limit": 0,
            "Weekly limit": 0,
            "Monthly limit": 0,
            "Yearly limit": limit
        })
    return {"message": "yearly alert set"}