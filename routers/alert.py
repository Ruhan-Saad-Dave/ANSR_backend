import os
import json
import firebase_admin
from firebase_admin import credentials, firestore
from fastapi import APIRouter 

from models.alert import Alert

alert_router = APIRouter()
try:
    # Check if the special environment variable is set.
    # This is the variable you will set in your cloud hosting provider's dashboard.
    creds_json_str = os.getenv("FIREBASE_CREDENTIALS_JSON")

    if creds_json_str is None:
        print("FIREBASE_CREDENTIALS_JSON environment variable not set.")
        # Optional: Fallback to a local file for local development
        # Make sure 'serviceAccountKey.json' is in your .gitignore!
        cred = credentials.Certificate(r"ansr.json")
    else:
        # Parse the JSON string from the environment variable
        creds_dict = json.loads(creds_json_str)
        cred = credentials.Certificate(creds_dict)

    # Initialize the app with the credentials
    firebase_admin.initialize_app(cred)
    print("Firebase App initialized successfully.")

except Exception as e:
    print(f"Error initializing Firebase App: {e}")
    # Handle the error appropriately, maybe exit the app if Firebase is critical
    db = None
else:
    # Get a reference to the Firestore database only if initialization was successful
    db = firestore.client()


@alert_router.post("/set_daily_alert", tags = ["alert"])
async def set_daily_alert(alert: Alert):
    id = alert.id
    limit = alert.limit
    doc_ref = db.collection('Limit Table').document('LimTab')
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
    doc_ref = db.collection('Limit Table').document('LimTab')
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
    doc_ref = db.collection('Limit Table').document('LimTab')
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
    doc_ref = db.collection('Limit Table').document('LimTab')
    doc = doc_ref.get()
    doc_ref.update({
        "Weekly limit" : doc.to_dict().get("Weekly limit"),
        "Yearly limit" : limit,
        "ID" : id, 
        "Daily Limit" : doc.to_dict().get("Daily Limit"), 
        "Monthly limit" : doc.to_dict().get("Monthly limit")
    })
    return {"message": "yearly alert set"}