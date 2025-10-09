import firebase_admin
from firebase_admin import credentials, firestore
from dotenv import load_dotenv
import os

load_dotenv()

def initialize_firebase():
    """
    Initializes the Firebase Admin SDK from environment variables.
    
    Returns:
        db: Firestore client instance if successful, else None.
    """
    global DB
    try:
        if not firebase_admin._apps:
            cred_dict = os.getenv("ANSR_KEY")
            cred = credentials.Certificate(cred_dict)
            firebase_admin.initialize_app(cred)
        
        db = firestore.client()
        print("✅ Firebase connection successful.")
        return db
    except Exception as e:
        print(f"🔥 Error initializing Firebase: {e}")
        print("   Please ensure your Firebase environment variables are set correctly.")
        return None
