# this file may get removed in the future


import firebase_admin
from firebase_admin import credentials, firestore
import os
import json
from dotenv import load_dotenv

load_dotenv()

def initialize_firebase():
    """
    Initializes the Firebase Admin SDK.
    """
    firebase_creds_json = os.getenv("FIREBASE_PRIVATE_KEY")
    if not firebase_creds_json:
        raise ValueError("FIREBASE_PRIVATE_KEY environment variable not set.")

    try:
        firebase_creds = json.loads(firebase_creds_json)
    except json.JSONDecodeError:
        raise ValueError("Failed to parse FIREBASE_PRIVATE_KEY. Make sure it's a valid JSON string.")

    cred = credentials.Certificate(firebase_creds)
    firebase_admin.initialize_app(cred)

def get_firestore_client():
    """
    Returns a Firestore client.
    """
    if not firebase_admin._apps:
        initialize_firebase()
    return firestore.client()
