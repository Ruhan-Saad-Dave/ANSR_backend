import re
from datetime import datetime
import json
from fastapi import HTTPException
from firebase_admin import firestore

# Assuming these services are in the same directory or accessible through the python path
from services.alert import limit_checker
from services.anomaly import detect_amount_anomalies_by_category, detect_time_anomalies
from core.setup import initialize_firebase 

DB = initialize_firebase()

def get_user_transactions(user_id):
    """Fetches recent transactions for a user from Firestore to be used in anomaly detection."""
    try:
        docs = DB.collection('Expense tracker').document(user_id).collection('transactions').limit(50).stream()
        # The anomaly script expects a list of dicts with 'Amount' and 'Category' keys
        transactions = []
        for doc in docs:
            data = doc.to_dict()
            transactions.append({
                "ID": doc.id, # The anomaly script uses 'ID' for the transaction id
                "Amount": data.get("amount"),
                "Category": data.get("category"),
                "timestamp": {"hour": data.get("timestamp", {}).get("hour")}
            })
        return transactions
    except Exception as e:
        print(f"Could not fetch historical transactions for user {user_id}: {e}")
        return []

def clean_raw_data(raw_data_string):
    """
    Cleans a raw data string and returns a dictionary with the cleaned data.

    Args:
        raw_data_string: A string in the format "ID, timestamp, application, sender (optional), exact message"

    Returns:
        A dictionary containing the cleaned data, or None if the format is invalid.
    """
    parts = [p.strip() for p in raw_data_string.split(',', 4)]
    if len(parts) < 4:
        return None  # Invalid format

    raw_id, raw_timestamp, application, raw_message = None, None, None, None
    raw_sender = None

    if len(parts) == 5:
        raw_id, raw_timestamp, application, raw_sender, raw_message = parts
    else:
        raw_id, raw_timestamp, application, raw_message = parts

    # 1. Parse timestamp
    try:
        # Assuming timestamp is in a recognizable format, e.g., ISO 8601
        dt_object = datetime.fromisoformat(raw_timestamp)
        timestamp = {
            "year": dt_object.year,
            "month": dt_object.month,
            "day": dt_object.day,
            "hour": dt_object.hour,
        }
    except ValueError:
        # Handle other potential timestamp formats or errors
        timestamp = {"year": None, "month": None, "day": None, "hour": None}

    # 2. Extract sender
    sender = raw_sender if raw_sender else "Unknown"

    # 3. Parse the message for payment details
    payment_method = "Unknown"
    payment_type = "Unknown"
    amount = None
    category = "Uncategorized"  # Default category
    message = raw_message

    # Simple regex to find amount (assuming format like $123.45 or 123.45)
    amount_match = re.search(r'(\d+\.?\d*)', raw_message)
    if amount_match:
        amount = float(amount_match.group(1))

    # Determine payment method
    if "credit" in raw_message.lower():
        payment_method = "credit"
    elif "upi" in raw_message.lower():
        payment_method = "UPI"

    # Determine payment type
    if "incoming" in raw_message.lower() or "received" in raw_message.lower():
        payment_type = "incoming"
    elif "outgoing" in raw_message.lower() or "sent" in raw_message.lower():
        payment_type = "outgoing"

    cleaned_data = {
        "id": raw_id,
        "timestamp": timestamp,
        "sender": sender,
        "payment_method": payment_method,
        "payment_type": payment_type,
        "amount": amount,
        "category": category,
        "message": message,
    }

    return cleaned_data

def _save_transaction(user_id, cleaned_data, is_anomaly):
    """Saves the processed transaction to Firestore."""
    if not DB:
        return "Firestore not initialized. Cannot save transaction."

    try:
        # Prepare the data according to the schema in data.txt
        ts = cleaned_data.get("timestamp", {})
        dt_object = datetime(ts.get("year", 1970), ts.get("month", 1), ts.get("day", 1))

        transaction_to_save = {
            "year": ts.get("year"),
            "month": ts.get("month"),
            "date": ts.get("day"),
            "day": dt_object.strftime("%A"),
            "amount": cleaned_data.get("amount"),
            "sender_name": cleaned_data.get("sender"),
            "payment_method": cleaned_data.get("payment_method"),
            "payment_type": cleaned_data.get("payment_type"),
            "anomaly": is_anomaly,
            "category": cleaned_data.get("category"),
            "message": cleaned_data.get("message"),
        }

        # Add the transaction to the subcollection, letting Firestore generate the ID
        DB.collection('Expense tracker').document(user_id).collection('transactions').add(transaction_to_save)
        return "Transaction saved successfully."

    except Exception as e:
        error_message = f"Error saving transaction for user {user_id}: {e}"
        print(error_message)
        return error_message

def _update_summary(user_id, transaction_data):
    """
    Updates the user's summary document in Firestore.
    Creates the document if it does not exist.
    """
    if not DB:
        return "Firestore not initialized."

    amount = transaction_data.get("amount")
    payment_type = transaction_data.get("payment_type")

    if not isinstance(amount, (int, float)) or amount <= 0:
        return "Invalid amount for summary update."

    try:
        doc_ref = DB.collection('summary').document(user_id)
        inc_out = firestore.Increment(amount if payment_type == 'outgoing' else 0)
        inc_in = firestore.Increment(amount if payment_type == 'incoming' else 0)
        inc_cashflow = firestore.Increment(amount if payment_type == 'incoming' else -amount)

        update_data = {
            'day_out': inc_out, 'week_out': inc_out, 'month_out': inc_out, 'year_out': inc_out,
            'day_in': inc_in, 'week_in': inc_in, 'month_in': inc_in, 'year_in': inc_in,
            'day_cashflow': inc_cashflow, 'week_cashflow': inc_cashflow, 'month_cashflow': inc_cashflow, 'year_cashflow': inc_cashflow
        }
        # Set with merge=True will create or update the document atomically.
        doc_ref.set(update_data, merge=True)
        return f"Summary updated for user {user_id}."

    except Exception as e:
        error_message = f"Error updating summary for user {user_id}: {e}"
        print(error_message)
        return error_message


def process_transaction(raw_data_string):
    """
    Processes a raw transaction string, cleans it, checks for alerts and anomalies,
    and saves it to the database.
    """
    cleaned_data = clean_raw_data(raw_data_string)
    user_id = cleaned_data.get("id") if cleaned_data else None

    # Stricter validation: Raise a 400 error if user_id is missing, empty, or just whitespace.
    if not user_id or not user_id.strip():
        raise HTTPException(status_code=400, detail="Invalid or empty user ID provided in raw data.")

    # If validation passes, proceed.
    print(f"--- Processing for valid User ID: {user_id} ---")

    alert_message = limit_checker(user_id)
    is_anomaly = False
    anomaly_message = "No anomalies detected"

    historical_transactions = get_user_transactions(user_id)
    
    anomaly_check_data = {
        "ID": cleaned_data["id"],
        "Amount": cleaned_data["amount"],
        "Category": cleaned_data["category"],
        "timestamp": cleaned_data["timestamp"]
    }
    all_transactions_for_anomaly_check = historical_transactions + [anomaly_check_data]

    high_amount_ids = detect_amount_anomalies_by_category(all_transactions_for_anomaly_check)
    unusual_time_ids = detect_time_anomalies(all_transactions_for_anomaly_check)

    reasons = []
    if user_id in high_amount_ids:
        reasons.append(f"Amount is significantly higher than other '{cleaned_data.get('category', 'N/A')}' expenses.")
    if user_id in unusual_time_ids:
        reasons.append("Transaction occurred at an unusual time (late night).")

    if reasons:
        is_anomaly = True
        anomaly_message = "Potential anomaly detected: " + " ".join(reasons)

    summary_status = _update_summary(user_id, cleaned_data)
    transaction_status = _save_transaction(user_id, cleaned_data, is_anomaly)
    firebase_save_status = f"Summary: {summary_status} | Transaction: {transaction_status}"
    print(f"--- Firebase Status: {firebase_save_status} ---")

    return {
        "cleaned_data": cleaned_data,
        "alert_message": alert_message,
        "anomaly_message": anomaly_message,
        "firebase_status": firebase_save_status
    }


if __name__ == '__main__':
    # Example Usage
    raw_data_1 = "user123, 2025-10-09T14:30:00, MyApp, John Doe, incoming credit payment of 50.00 for groceries"
    raw_data_2 = "user123, 2025-10-09T23:00:00, YourApp, , outgoing upi payment of 2500.50 for rent" # high amount but recurring
    raw_data_3 = "user456, 2025-10-10T02:00:00, AnotherApp, Jane Smith, sent 100.00 via upi" # unusual time

    processed_1 = process_transaction(raw_data_1)
    processed_2 = process_transaction(raw_data_2)
    processed_3 = process_transaction(raw_data_3)

    print(json.dumps(processed_1, indent=2))
    print(json.dumps(processed_2, indent=2))
    print(json.dumps(processed_3, indent=2))