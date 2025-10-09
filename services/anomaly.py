import firebase_admin
from firebase_admin import credentials, firestore
import numpy as np
from collections import defaultdict



def fetch_transactions(db):
    """
    Fetches all documents from the specified Firestore collection.

    Args:
        db: The initialized Firestore client.
    
    Returns:
        list: A list of transaction dictionaries, or an empty list if an error occurs or collection is empty.
    """
    try:
        collection_ref = db.collection('Expense_tracker').document('Tracker').collection('Tracker')
        docs = collection_ref.stream()
        
        transactions = [doc.to_dict() for doc in docs]
        
        if not transactions:
            print("⚠️ Warning: No documents found in 'Expense_tracker/Tracker/Tracker'.")
        else:
            print(f"📊 Found {len(transactions)} transactions.")
        return transactions
    except Exception as e:
        print(f"🔥 Error fetching transactions: {e}")
        return []

def detect_amount_anomalies_by_category(transactions):
    """
    Detects transactions with unusually high amounts within their category using the IQR method,
    while ignoring known recurring large payments like rent.

    Args:
        transactions (list): A list of transaction dictionaries.
    
    Returns:
        set: A set of transaction IDs that are considered high-amount anomalies.
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

        # Rule-Based Filtering: Check if the transaction message contains any recurring expense keywords.
        if any(keyword in message.lower() for keyword in RECURRING_EXPENSE_KEYWORDS):
            continue # Skip this transaction from amount anomaly check

        category = tx.get('Category', 'Uncategorized')
        categorized_transactions[category].append(tx)

    anomaly_ids = set()
    
    # Perform IQR analysis on each category
    for category, tx_list in categorized_transactions.items():
        if len(tx_list) < 5:
            # Not enough data in this category for a reliable statistical check
            continue

        amounts = [tx['Amount'] for tx in tx_list if 'Amount' in tx and tx['Amount'] is not None]
        if not amounts:
            continue

        q1 = np.percentile(amounts, 25)
        q3 = np.percentile(amounts, 75)
        iqr = q3 - q1
        
        # A multiplier of 2.0 is conservative. Use 1.5 for more aggressive flagging.
        upper_bound = q3 + (iqr * 2.0)
        
        print(f"     - Category '{category}': Upper threshold set at ₹{upper_bound:,.2f}")

        for tx in tx_list:
            if tx.get('Amount', 0) > upper_bound:
                anomaly_ids.add(tx.get('ID'))
                
    return anomaly_ids

def detect_time_anomalies(transactions):
    """
    Detects transactions that occur at unusual times (e.g., late at night).

    Args:
        transactions (list): A list of transaction dictionaries.
    
    Returns:
        set: A set of transaction IDs that are considered time-based anomalies.
    """
    LATE_NIGHT_START = 1  # 1 AM
    LATE_NIGHT_END = 5    # 5 AM

    anomaly_ids = set()
    for tx in transactions:
        # The 'hour' field should be extracted from the timestamp during data cleaning
        hour = tx.get('timestamp', {}).get('hour')
        if isinstance(hour, int) and (LATE_NIGHT_START <= hour <= LATE_NIGHT_END):
            anomaly_ids.add(tx.get('ID'))
    
    print("   - Time Anomaly Detection: Flagging transactions between 1 AM and 5 AM.")
    return anomaly_ids


def main():
    """
    Main function to run the anomaly detection process.
    """
    print("--- Starting Transaction Anomaly Detector ---")
    
    # IMPORTANT: Update this path to your service account key file
    SERVICE_ACCOUNT_KEY_PATH = 'path/to/your/serviceAccountKey.json'
    
    db = initialize_firebase(SERVICE_ACCOUNT_KEY_PATH)
    
    if not db:
        print("\n--- Halting execution due to Firebase connection error. ---")
        return

    transactions = fetch_transactions(db)
    
    if not transactions:
        print("\n--- Halting execution as there are no transactions to analyze. ---")
        return
        
    print("\n🔬 Running improved anomaly detection algorithms...")
    # Use the new categorical amount detection function
    high_amount_ids = detect_amount_anomalies_by_category(transactions)
    unusual_time_ids = detect_time_anomalies(transactions)
    
    print("\n--- Analysis Complete ---")
    
    flagged_anomalies = []
    for tx in transactions:
        reasons = []
        tx_id = tx.get('ID')
        
        if tx_id in high_amount_ids:
            reasons.append(f"Amount is significantly higher than other '{tx.get('Category', 'N/A')}' expenses.")
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
            amount = tx.get('Amount', 'N/A')
            category = tx.get('Category', 'N/A')
            ts = tx.get('timestamp', {})
            date_str = f"{ts.get('day', '?')}/{ts.get('month', '?')}/{ts.get('year', '?')} at {ts.get('hour', '?')}:00"
            
            print(f"--- Anomaly #{i} ---")
            print(f"  Transaction ID: {tx.get('ID', 'N/A')}")
            print(f"  Details: ₹{amount:,.2f} in '{category}' on {date_str}")
            print("  Reasons:")
            for reason in anomaly['reasons']:
                print(f"    - {reason}")
            print("-" * 20)
            
    print("\n--- End of Report ---")

if __name__ == '__main__':
    main()