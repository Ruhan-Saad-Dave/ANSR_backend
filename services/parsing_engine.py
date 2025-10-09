from flask import Flask, request, jsonify
import re
from datetime import datetime
import json
import firebase_admin
from firebase_admin import credentials, firestore

# --- 1. FIREBASE INITIALIZATION ---
try:
    cred = credentials.Certificate("ansr-7f506-firebase-adminsdk-fbsvc-052e7ed895.json")
    firebase_admin.initialize_app(cred)
    db = firestore.client()
except Exception as e:
    print(f"Firebase initialization failed: {e}\nPlease ensure 'serviceAccountKey.json' is present and valid.")
    db = None

# --- 2. PATTERN LIBRARY ---
TRANSACTION_PATTERNS = [
    {"name": "P2P UPI Credit", "type": "credit", "method": "UPI",
     "regex": r"(?P<vendor>.+?)\s+paid you\s+(?:₹|Rs\.?|INR)\s*(?P<amount>[\d,]+\.?\d{1,2})\.?"},
    {"name": "Generic Debit", "type": "debit", "method": "Bank Account",
     "regex": r"(?:Rs\.?|INR)\s*(?P<amount>[\d,]+\.?\d{1,2})\s+debited\s+from\s+.+a/c\s+(?P<account>\w*\d+)\.\s+Info:\s*(?P<vendor>.+?)\."},
    {"name": "Credit Card Purchase", "type": "debit", "method": "Card",
     "regex": r"Transaction\s+of\s+(?:Rs\.?|INR)\s*(?P<amount>[\d,]+\.?\d{1,2})\s+at\s+(?P<vendor>.+?)\s+on\s+.+Card\s+ending\s+(?P<account>\d{4})\."},
    {"name": "UPI Debit", "type": "debit", "method": "UPI",
     "regex": r"Paid\s+(?:Rs\.?|INR)\s*(?P<amount>[\d,]+\.?\d{1,2})\s+to\s+(?P<vendor>.+?)\s+from\s+.+a/c\s+via\s+UPI"},
    {"name": "UPI Credit", "type": "credit", "method": "UPI",
     "regex": r"Received\s+(?:Rs\.?|INR)\s*(?P<amount>[\d,]+\.?\d{1,2})\s+from\s+(?P<vendor>.+?)\s+in\s+.+a/c\s+via\s+UPI"},
    {"name": "Generic Credit", "type": "credit", "method": "Bank Account",
     "regex": r"(?:Rs\.?|INR)\s*(?P<amount>[\d,]+\.?\d{1,2})\s+credited\s+to\s+a/c\s+(?P<account>\w*\d+)\.\s+.+from\s+(?P<vendor>.+?)\."},
]


# --- 3. PARSING & TRANSFORMATION FUNCTIONS ---
def parse_message_details(message):
    for pattern in TRANSACTION_PATTERNS:
        match = re.search(pattern["regex"], message, re.IGNORECASE)
        if match:
            data = match.groupdict()
            return {
                "amount": float(data.get("amount", "0").replace(",", "")),
                "vendor": data.get("vendor", "Unknown").strip(),
                "payment_type": "income" if pattern["type"] == "credit" else "expense",
                "payment_method": pattern.get("method", "Unknown")
            }
    return None


def format_transaction_data(raw_data_string):
    # <<< CHANGE HERE: New logic to parse the string with UserID at the start
    parts = [p.strip() for p in raw_data_string.split(',', 5)]
    if len(parts) < 6:  # Now requires 6 parts: UserID, ID, Timestamp, App, Sender, Message
        return None, None  # Invalid format

    user_id, raw_id, raw_timestamp, application, raw_sender, raw_message = parts

    try:
        dt_object = datetime.fromisoformat(raw_timestamp)
    except ValueError:
        return None, None  # Invalid timestamp format

    details = parse_message_details(raw_message)
    if not details:
        return None, None  # Message is not a recognized transaction

    formatted_data = {
        "year": dt_object.year,
        "month": dt_object.month,
        "date": dt_object.day,
        "day": dt_object.strftime("%A"),
        "amount": details["amount"],
        "sender_name": details["vendor"],
        "payment_method": details["payment_method"],
        "payment_type": details["payment_type"],
        "category": "Uncategorized",
        "message": raw_message,
        "source_app": application
    }
    return formatted_data, user_id


# --- 4. DATABASE FUNCTION ---
def add_transaction_to_db(formatted_transaction, user_id):
    if not db:
        print("Firestore not initialized. Cannot save data.")
        return False
    try:
        payment_type = formatted_transaction.get("payment_type")

        if payment_type == 'income':
            collection_name = 'Income'
        elif payment_type == 'expense':
            collection_name = 'Expense tracker'
        else:
            print(f"⚠️ Unknown payment type '{payment_type}'. Not saving to DB.")
            return False

        user_doc_ref = db.collection(collection_name).document(user_id)
        user_doc_ref.collection('transactions').add(formatted_transaction)

        print(f"✅ Successfully wrote transaction for UserID '{user_id}' in '{collection_name}'.")
        return True
    except Exception as e:
        print(f"❌ Error writing to Firestore: {e}")
        return False


# --- 5. FLASK APPLICATION ---
app = Flask(__name__)


@app.route('/parse', methods=['POST'])
def parse_endpoint():
    data = request.get_json()
    # <<< CHANGE HERE: Simplified request validation
    if not data or 'raw_string' not in data:
        return jsonify({"error": "Missing 'raw_string' in request body"}), 400

    raw_string = data['raw_string']

    # Transform the raw data, which now returns the UserID as well
    formatted_data, user_id = format_transaction_data(raw_string)

    if not formatted_data:
        return jsonify({"error": "Failed to parse transaction from raw_string"}), 400

    # Save the formatted data to the database
    db_success = add_transaction_to_db(formatted_data, user_id)
    if not db_success:
        return jsonify({"error": "Data parsed but failed to save to database"}), 500

    return jsonify(formatted_data)


if __name__ == '__main__':
    app.run(debug=True, port=5000)
