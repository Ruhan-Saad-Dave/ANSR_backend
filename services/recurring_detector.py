from collections import defaultdict
from datetime import date, timedelta
import numpy as np
from core.setup import initialize_firebase

DB = initialize_firebase()
MIN_TRANSACTIONS = 3  # Minimum number of transactions to be considered a potential subscription
TOLERANCE_PERCENT = 0.10  # Amount can vary by +/- 10%

# Define intervals in days and their tolerance
INTERVALS = {
    "weekly": (7, 1),
    "monthly": (30.5, 3),
    "quarterly": (91.5, 7),
    "yearly": (365, 15),
}

def _fetch_user_transactions(user_id):
    """Fetches all outgoing transactions for a given user."""
    try:
        docs = DB.collection('Expense tracker').document(user_id).collection('transactions').where('payment_type', '==', 'outgoing').stream()
        transactions = []
        for doc in docs:
            data = doc.to_dict()
            # Ensure transaction has the necessary fields
            if all(k in data for k in ['year', 'month', 'date', 'amount', 'sender_name']):
                data['tx_date'] = date(data['year'], data['month'], data['date'])
                transactions.append(data)
        return transactions
    except Exception as e:
        print(f"Error fetching transactions for user {user_id}: {e}")
        return []

def detect_recurring(user_id):
    """
    Analyzes a user's transactions to detect recurring payments.
    """
    transactions = _fetch_user_transactions(user_id)
    if not transactions:
        return []

    # Group transactions by recipient (sender_name)
    grouped_by_recipient = defaultdict(list)
    for tx in transactions:
        grouped_by_recipient[tx['sender_name']].append(tx)

    detected_recurring = []

    for recipient, tx_list in grouped_by_recipient.items():
        if len(tx_list) < MIN_TRANSACTIONS:
            continue

        # --- 1. Check for consistent amount ---
        amounts = [tx['amount'] for tx in tx_list]
        median_amount = np.median(amounts)
        lower_bound = median_amount * (1 - TOLERANCE_PERCENT)
        upper_bound = median_amount * (1 + TOLERANCE_PERCENT)

        consistent_amounts = [a for a in amounts if lower_bound <= a <= upper_bound]
        # If less than 80% of transactions have a consistent amount, skip
        if len(consistent_amounts) / len(amounts) < 0.8:
            continue

        # --- 2. Check for regular time intervals ---
        tx_list.sort(key=lambda x: x['tx_date'])
        deltas = [(tx_list[i+1]['tx_date'] - tx_list[i]['tx_date']).days for i in range(len(tx_list) - 1)]
        
        if not deltas:
            continue

        median_delta = np.median(deltas)

        for name, (avg_days, tolerance) in INTERVALS.items():
            if abs(median_delta - avg_days) <= tolerance:
                # We found a matching interval
                detected_recurring.append({
                    "recipient": recipient,
                    "amount": round(median_amount, 2),
                    "frequency": name,
                    "transaction_count": len(tx_list)
                })
                break # Move to the next recipient
    
    return detected_recurring 

if __name__ == '__main__':
    print("Recurring detector service ready. Run with a user_id to test.")
