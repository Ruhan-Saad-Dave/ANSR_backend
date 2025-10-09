import os
import re
import json
from datetime import datetime
from dotenv import load_dotenv

import firebase_admin
from firebase_admin import credentials, firestore
from flask import Flask, request, jsonify

from langchain_google_genai import ChatGoogleGenerativeAI
from pydantic import BaseModel, Field

# --- CONFIGURATION & SETUP ---
load_dotenv()

# 1a. Firebase Initialization
try:
    cred = credentials.Certificate("ansr-7f506-firebase-adminsdk-fbsvc-052e7ed895.json")
    firebase_admin.initialize_app(cred)
    db = firestore.client()
    print("--- Firebase Initialized Successfully ---")
except Exception as e:
    print(f"Firebase initialization failed: {e}\nPlease ensure 'serviceAccountKey.json' is present and valid.")
    db = None

# 1b. LangChain (Gemini) Initialization
api_key = os.getenv("GOOGLE_API_KEY")
if not api_key:
    raise ValueError("GOOGLE_API_KEY environment variable not set.")

# --- 2. REGEX PARSER ---
TRANSACTION_PATTERNS = [
    {"name": "P2P UPI Credit", "type": "credit", "method": "UPI",
     "regex": r"(?P<vendor>.+?)\s+paid you\s+(?:₹|Rs\.?|INR)\s*(?P<amount>[\d,]+\.?\d{1,2})\.?"},
    {"name": "BOI UPI Debit", "type": "debit", "method": "UPI",
     "regex": r"(?:Rs\.?|INR)\s*(?P<amount>[\d,]+\.?\d{1,2})\s+debited\s+A/c(?P<account>\w*\d+)\s+and credited to\s+(?P<vendor>.+?)\s+via\s+UPI"},
    {"name": "Credit Card Purchase", "type": "debit", "method": "Card",
     "regex": r"Transaction\s+of\s+(?:Rs\.?|INR)\s*(?P<amount>[\d,]+\.?\d{1,2})\s+at\s+(?P<vendor>.+?)\s+on\s+.+Card\s+ending\s+(?P<account>\d{4})\."},
    {"name": "UPI Debit", "type": "debit", "method": "UPI",
     "regex": r"Paid\s+(?:Rs\.?|INR)\s*(?P<amount>[\d,]+\.?\d{1,2})\s+to\s+(?P<vendor>.+?)\s+from\s+.+a/c\s+via\s+UPI"},
]


def parse_with_regex(message):
    for pattern in TRANSACTION_PATTERNS:
        match = re.search(pattern["regex"], message, re.IGNORECASE)
        if match:
            data = match.groupdict()
            return {
                "amount": float(data.get("amount", "0").replace(",", "")),
                "sender_name": data.get("vendor", "Unknown").strip(),
                "payment_type": "income" if pattern["type"] == "credit" else "expense",
                "payment_method": pattern.get("method", "Unknown"),
                "category": "Uncategorized",
            }
    return None


# --- 3. LLM PARSER ---
class TransactionDetails(BaseModel):
    amount: float = Field(description="The numeric amount of the transaction.")
    sender_name: str = Field(description="The name of the person or vendor involved.")
    payment_method: str = Field(description="The method of payment (e.g., UPI, Card, Bank Account).")
    payment_type: str = Field(description="The type of transaction, either 'income' or 'expense'.")
    category: str = Field(description="A suggested category (e.g., Food, Shopping, Salary, Travel).")


def parse_with_llm(message: str):
    llm = ChatGoogleGenerativeAI(model="gemini-1.5-flash", temperature=0)
    structured_llm = llm.with_structured_output(TransactionDetails)
    prompt = f"Analyze the following financial transaction message and extract the details. Message: \"{message}\""
    try:
        response = structured_llm.invoke(prompt)
        response_dict = response.dict()
        response_dict['message'] = message
        return response_dict
    except Exception as e:
        print(f"LLM parsing failed: {e}")
        return None


# --- 4. HYBRID PARSER CONTROLLER ---
def parse_transaction(message):
    print("--- Attempting to parse with Regex... ---")
    result = parse_with_regex(message)
    if result:
        print("--- Regex parsing successful. ---")
        result['message'] = message
        return result

    print("--- Regex failed. Falling back to LLM parser... ---")
    result = parse_with_llm(message)
    if result:
        print("--- LLM parsing successful. ---")
    return result


# --- 5. MAIN DATA FORMATTING & DATABASE FUNCTIONS ---
def format_transaction_data(timestamp_str, app_name, raw_message):
    # <<< CHANGE HERE: This function is now much simpler
    try:
        dt_object = datetime.fromisoformat(timestamp_str)
    except (ValueError, TypeError):
        return None

    # Use the hybrid parser to get transaction details
    details = parse_transaction(raw_message)
    if not details:
        return None

    # Assemble the final, flat dictionary for Firestore
    final_data = {
        "year": dt_object.year,
        "month": dt_object.month,
        "date": dt_object.day,
        "day": dt_object.strftime("%A"),
        "amount": details.get("amount"),
        "sender_name": details.get("sender_name"),
        "payment_method": details.get("payment_method"),
        "payment_type": details.get("payment_type"),
        "category": details.get("category"),
        "message": details.get("message"),
        "source_app": app_name
    }
    return final_data


def add_transaction_to_db(formatted_transaction, user_id):
    if not db: return False
    try:
        payment_type = formatted_transaction.get("payment_type")
        if payment_type == 'income':
            collection_name = 'Income'
        elif payment_type == 'expense':
            collection_name = 'Expenses'
        else:
            return False

        user_doc_ref = db.collection(collection_name).document(user_id)
        user_doc_ref.collection('transactions').add(formatted_transaction)
        print(f"✅ DB Write: Successfully wrote transaction for UserID '{user_id}'.")
        return True
    except Exception as e:
        print(f"❌ DB Write Error: {e}")
        return False


# --- 6. FLASK APPLICATION ---
app = Flask(__name__)


@app.route('/parse', methods=['POST'])
def parse_endpoint():
    # <<< CHANGE HERE: Updated to handle new JSON structure
    data = request.get_json()
    required_fields = ["user_id", "timestamp", "application_name", "raw_message"]
    if not data or not all(field in data for field in required_fields):
        return jsonify({"error": f"Missing required fields: {required_fields}"}), 400

    user_id = data['user_id']

    # Pass the individual fields to the formatting function
    formatted_data = format_transaction_data(
        timestamp_str=data['timestamp'],
        app_name=data['application_name'],
        raw_message=data['raw_message']
    )

    if not formatted_data:
        return jsonify({"error": "Failed to parse transaction from raw_message"}), 400

    db_success = add_transaction_to_db(formatted_data, user_id)
    if not db_success:
        return jsonify({"error": "Data parsed but failed to save to database"}), 500

    return jsonify(formatted_data)


if __name__ == '__main__':
    app.run(debug=True, port=5000)
