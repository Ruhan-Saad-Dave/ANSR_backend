import os
import numpy as np
from collections import defaultdict
from dotenv import load_dotenv
from supabase import create_client, Client
from dateutil.parser import parse as parse_datetime
from core.setup import initialize_firebase

# --- 2. Data Fetching ---

def fetch_transactions(db: Client):
    """
    Fetches all documents from the 'transaction' table.

    Args:
        db: The initialized Supabase client.

    Returns:
        list: A list of transaction dictionaries, or an empty list if an error occurs or table is empty.
    """
    try:
        # Select all columns from the 'transaction' table
        response = db.table('transaction').select('*').execute()

        transactions = response.data

        if not transactions:
            print("⚠️ Warning: No documents found in 'transaction' table.")
        else:
            print(f"📊 Found {len(transactions)} transactions.")
        return transactions
    except Exception as e:
        print(f"🔥 Error fetching transactions: {e}")
        return []


# --- 3. Anomaly Detection Algorithms ---

def detect_amount_anomalies_by_category(transactions):
    """
    Detects transactions with unusually high amounts within their category using the IQR method,
    while ignoring known recurring large payments like rent.
    """
    print("   - Running Categorical Amount Anomaly Detection...")

    # Keywords to identify and exclude known large, recurring payments from anomaly detection.
    RECURRING_EXPENSE_KEYWORDS = ['rent', 'housing', 'monthly fee', 'subscription']

    # Group transactions by category, excluding known recurring ones from the check.
    categorized_transactions = defaultdict(list)

    for tx in transactions:
        # Ensure message is a string before calling .lower()
        message = tx.get('message', '')
        if not isinstance(message, str):
            message = str(message)

        # Rule-Based Filtering
        if any(keyword in message.lower() for keyword in RECURRING_EXPENSE_KEYWORDS):
            continue  # Skip this transaction from amount anomaly check

        # Use 'category' field from your schema
        category = tx.get('category', 'Uncategorized')
        categorized_transactions[category].append(tx)

    anomaly_ids = set()

    # Perform IQR analysis on each category
    for category, tx_list in categorized_transactions.items():
        if len(tx_list) < 5:
            continue

        # Use 'amount' field from your schema
        amounts = [tx['amount'] for tx in tx_list if 'amount' in tx and tx['amount'] is not None]
        if not amounts:
            continue

        q1 = np.percentile(amounts, 25)
        q3 = np.percentile(amounts, 75)
        iqr = q3 - q1

        upper_bound = q3 + (iqr * 2.0)

        print(f"     - Category '{category}': Upper threshold set at ₹{upper_bound:,.2f}")

        for tx in tx_list:
            # Use 'amount' and 'transaction_id' fields
            if tx.get('amount', 0) > upper_bound:
                anomaly_ids.add(tx.get('transaction_id'))

    return anomaly_ids


def detect_time_anomalies(transactions):
    """
    Detects transactions that occur at unusual times (e.g., late at night).
    """
    LATE_NIGHT_START = 1  # 1 AM
    LATE_NIGHT_END = 5  # 5 AM

    anomaly_ids = set()
    for tx in transactions:
        # Use 'created_at' field from your schema
        timestamp_str = tx.get('created_at')
        if not timestamp_str:
            continue

        try:
            # Parse the ISO 8601 timestamp string from Supabase
            dt = parse_datetime(timestamp_str)
            hour = dt.hour
        except Exception:
            # Skip if the timestamp is in an unexpected format
            continue

        if LATE_NIGHT_START <= hour <= LATE_NIGHT_END:
            # Use 'transaction_id' field
            anomaly_ids.add(tx.get('transaction_id'))

    print("   - Time Anomaly Detection: Flagging transactions between 1 AM and 5 AM.")
    return anomaly_ids


def main():
    """
    Main function to run the anomaly detection process.
    """
    print("--- Starting Transaction Anomaly Detector ---")

    db = initialize_firebase()

    if not db:
        print("\n--- Halting execution due to Supabase connection error. ---")
        return

    transactions = fetch_transactions(db)

    if not transactions:
        print("\n--- Halting execution as there are no transactions to analyze. ---")
        return

    print("\n🔬 Running improved anomaly detection algorithms...")
    high_amount_ids = detect_amount_anomalies_by_category(transactions)
    unusual_time_ids = detect_time_anomalies(transactions)

    print("\n--- Analysis Complete ---")

    flagged_anomalies = []
    for tx in transactions:
        reasons = []
        # Use 'transaction_id' field
        tx_id = tx.get('transaction_id')

        if tx_id in high_amount_ids:
            # Use 'category' field
            reasons.append(f"Amount is significantly higher than other '{tx.get('category', 'N/A')}' expenses.")
        if tx_id in unusual_time_ids:
            reasons.append("Transaction occurred at an unusual time (late night).")

        if reasons:
            flagged_anomalies.append({'transaction': tx, 'reasons': reasons})

    if not flagged_anomalies:
        print("\n✅ No anomalies detected. All transactions appear normal.")
    else:
        print(f"\n🚨 Found {len(flagged_anomalies)} potential anomalies:\n")
        for i, anomaly in enumerate(flagged_anomalies, 1):
            tx = anomaly['transaction']
            # Use schema fields
            amount = tx.get('amount', 'N/A')
            category = tx.get('category', 'N/A')
            date_str = tx.get('created_at', 'N/A')  # The ISO string is fine for a report

            print(f"--- Anomaly #{i} ---")
            print(f"  Transaction ID: {tx.get('transaction_id', 'N/A')}")
            print(f"  Details: ₹{amount:,.2f} in '{category}' on {date_str}")
            print("  Reasons:")
            for reason in anomaly['reasons']:
                print(f"    - {reason}")
            print("-" * 20)

    print("\n--- End of Report ---")


if __name__ == '__main__':
    main()