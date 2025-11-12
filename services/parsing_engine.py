import re

from datetime import datetime
from pydantic import BaseModel, Field
from langchain_google_genai import ChatGoogleGenerativeAI
# Note: Removed 'supabase: Client' import. This file no longer knows about the DB.


# --- 1. REGEX PATTERNS (Unchanged) ---
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


# --- 2. REGEX PARSER (Unchanged) ---
def parse_with_regex(message: str):
    """
    Parses a message using a list of predefined regex patterns.
    """
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


# --- 3. LLM PARSER (Unchanged) ---
class TransactionDetails(BaseModel):
    amount: float = Field(description="The numeric amount of the transaction.")
    sender_name: str = Field(description="The name of the person or vendor involved.")
    payment_method: str = Field(description="The method of payment (e.g., UPI, Card, Bank Account).")
    payment_type: str = Field(description="The type of transaction, either 'income' or 'expense'.")
    category: str = Field(description="A suggested category (e.g., Food, Shopping, Salary, Travel).")


def parse_with_llm(message: str):
    """
    Parses a message using a structured output LLM.
    """
    # Assuming the Google API key is set in the environment variables
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


# --- 4. HYBRID PARSER CONTROLLER (Unchanged) ---
def parse_transaction(message: str):
    """
    Parses a transaction message using a hybrid approach.
    First, it tries with regex. If that fails, it falls back to an LLM.
    This function returns a dictionary (JSON) or None.
    """
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

