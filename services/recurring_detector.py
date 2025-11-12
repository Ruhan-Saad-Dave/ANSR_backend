from collections import defaultdict
from datetime import date, timedelta
import numpy as np
from core.setup import initialize_firebase  # Using your custom initializer
from dateutil.parser import parse as parse_datetime  # For parsing timestamps

# --- 1. SUPABASE INITIALIZATION ---
DB = initialize_firebase()
MIN_TRANSACTIONS = 3  # Minimum number of transactions to be considered a potential subscription
TOLERANCE_PERCENT = 0.10  # Amount can vary by +/- 10%

# Define intervals in days and their tolerance
INTERVALS = {
    "weekly": (7, 1),
    "monthly": (30.5, 3),  # Using 30.5 as an average
    "quarterly": (91.5, 7),  # Using 91.5 as an average
    "yearly": (365, 15),
}


# --- 2. DATA FETCHING (MODIFIED FOR SUPABASE) ---
def _fetch_user_transactions(user_id):
    """Fetches all expense transactions for a given user from Supabase."""
    try:
        # Query the 'transaction' table for 'expense' types
        response = DB.table('transaction').select('*') \
            .eq('user_id', user_id) \
            .eq('payment_type', 'expense') \
            .execute()

        transactions = []
        if not response.data:
            return []

        for data in response.data:
            # Ensure transaction has the necessary fields
            if all(k in data for k in ['created_at', 'amount', 'sender_name']):
                try:
                    # Parse the 'created_at' timestamp string into a date object
                    data['tx_date'] = parse_datetime(data['created_at']).date()
                    transactions.append(data)
                except Exception as e:
                    print(f"Skipping transaction due to date parse error: {e}")

        return transactions
    except Exception as e:
        print(f"Error fetching transactions for user {user_id}: {e}")
        return []


# --- 3. RECURRING DETECTION (LOGIC UNCHANGED) ---
def detect_recurring(user_id):
    """
    Analyzes a user's transactions to detect recurring payments.
    This logic is database-agnostic and remains unchanged.
    """
    transactions = _fetch_user_transactions(user_id)
    if not transactions:
        print(f"No transactions found for user {user_id} to analyze.")
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
        deltas = [(tx_list[i + 1]['tx_date'] - tx_list[i]['tx_date']).days for i in range(len(tx_list) - 1)]

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
                break  # Move to the next recipient

    return detected_recurring


# --- 4. EXECUTION (UNCHANGED) ---
if __name__ == '__main__':
    print("--- Starting Recurring Transaction Detector ---")
    if not DB:
        print("Halting: Supabase DB not initialized. Check core.setup and .env file.")
    else:
        # --- Test with a user ID ---
        test_user_id = 123  # Replace with a valid user_id from your Supabase DB
        print(f"Detecting recurring payments for user: {test_user_id}")

        subscriptions = detect_recurring(test_user_id)

        if not subscriptions:
            print("No recurring subscriptions found.")
        else:
            print(f"\n--- Found {len(subscriptions)} Potential Subscriptions ---")
            for sub in subscriptions:
                print(f"  - Recipient: {sub['recipient']}")
                print(f"    Amount: ~₹{sub['amount']}")
                print(f"    Frequency: {sub['frequency']}")
                print(f"    Based on: {sub['transaction_count']} transactions")
                print("-" * 20)

    print("\n--- Detector finished. ---")