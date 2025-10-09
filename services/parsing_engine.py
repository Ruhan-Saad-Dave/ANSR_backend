
import re
from datetime import datetime

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
    category = None  # Optional
    message = raw_message  # Optional

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
        "ID": raw_id,
        "timestamp": timestamp,
        "sender": sender,
        "payment_method": payment_method,
        "payment_type": payment_type,
        "amount": amount,
        "category": category,
        "message": message,
    }

    return cleaned_data


if __name__ == '__main__':
    # Example Usage
    raw_data_1 = "1, 2025-10-09T14:30:00, MyApp, John Doe, incoming credit payment of 50.00 for groceries"
    raw_data_2 = "2, 2025-10-09T15:00:00, YourApp, , outgoing upi payment of 25.50"
    raw_data_3 = "3, 2025-10-09T16:00:00, AnotherApp, Jane Smith, sent 100.00 via upi"

    cleaned_1 = clean_raw_data(raw_data_1)
    cleaned_2 = clean_raw_data(raw_data_2)
    cleaned_3 = clean_raw_data(raw_data_3)

    import json
    print(json.dumps(cleaned_1, indent=2))
    print(json.dumps(cleaned_2, indent=2))
    print(json.dumps(cleaned_3, indent=2))
