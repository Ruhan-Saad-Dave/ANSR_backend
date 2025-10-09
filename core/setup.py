import firebase_admin
from firebase_admin import credentials, firestore

def initialize_firebase(service_account_key_path):
    """
    Initializes the Firebase Admin SDK.

    Args:
        service_account_key_path (str): The file path to your Firebase service account key JSON file.
    
    Returns:
        db: Firestore client instance if successful, else None.
    """
    try:
        if not firebase_admin._apps:
            cred = credentials.Certificate(service_account_key_path)
            firebase_admin.initialize_app(cred)
        
        db = firestore.client()
        print("✅ Firebase connection successful.")
        return db
    except Exception as e:
        print(f"🔥 Error initializing Firebase: {e}")
        print("   Please ensure the path to your service account key is correct and the file is valid.")
        return None