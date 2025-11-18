import collections
from datetime import datetime, timedelta

from core.setup import initialize_supabase

# configuration setup
db = initialize_supabase()

def get_summary(user_id: str) -> str:
    summary_data = db.table("summary").select("*").eq("user_id", user_id).execute()
    if summary_data.data:
        summary = summary_data.data[0].get("summary_text", "No summary available.")
        return f"Summary for user {user_id}:\n{summary}"
    else:
        return f"No summary found for user {user_id}."
    
def get_limit(user_id: str) -> str:
    limit_data = db.table("limit").select("*").eq("user_id", user_id).execute()
    if limit_data.data:
        limit = limit_data.data[0].get("limit_amount", "No limit set.")
        return f"Limit for user {user_id}:\n{limit}"
    else:
        return f"No limit found for user {user_id}."
    
def get_pending(user_id: str) -> str:
    pending_data = db.table("pending").select("amount", "other_user", "is_current_debtor").eq("user_id", user_id).execute()
    if pending_data.data:
        pending_transactions = pending_data.data
        net_balances = collections.defaultdict(float)

        for transaction in pending_transactions:
            amount = transaction.get('amount', 0)
            other_user = transaction.get('other_user')
            is_current_debtor = transaction.get('is_current_debtor', False)

            if other_user is None:
                # Skip invalid transactions
                print(f"Warning: Skipping transaction with missing 'other_user': {transaction}")
                continue

            if is_current_debtor is False:
                # If 'is_current_debtor' is False, the other user owes us (we paid), so we add the amount.
                net_balances[other_user] += amount
            else:
                # If 'is_current_debtor' is True, we owe the other user, so we subtract the amount.
                net_balances[other_user] -= amount
        
        if not net_balances:
            return f"No valid pending transactions found for user {user_id}."

        return f"Pending transactions: {dict(net_balances)}"
    else:
        return f"No pending transactions found for user {user_id}."
    
def get_transactions(
    user_id: str,
    start_date: str = None,
    end_date: str = None,
    category: str = None,
    payment_type: str = None,  # 'income' or 'expense'
    limit: int = 20
) -> str:
    """
    Retrieves user transactions with optional filters.
    Supports filtering by date range, category, and payment_type ('income' or 'expense').
    Dates should be in YYYY-MM-DD format.
    If no dates are given, it defaults to the last 30 days.
    """
    try:
        # Based on your schema, I am assuming the primary date column is named 'timestamp'
        # and is a text string or a proper timestamp type that can be filtered on.
        query = db.table("transaction").select("*").eq("user_id", user_id)

        # Date filtering
        if start_date:
            query = query.gte("timestamp", start_date)
        if end_date:
            # To make the end_date inclusive, we can aim for the end of that day
            query = query.lte("timestamp", f"{end_date} 23:59:59")

        # Default to last 30 days if no dates are provided
        if not start_date and not end_date:
            thirty_days_ago = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
            query = query.gte("timestamp", thirty_days_ago)

        # Category filtering
        if category:
            query = query.ilike("category", f"%{category}%")

        # Payment type filtering
        if payment_type and payment_type.lower() in ['income', 'expense']:
            query = query.eq("payment_type", payment_type.lower())

        # Order by timestamp descending and apply limit
        response = query.order("timestamp", desc=True).limit(limit).execute()

        if response.data:
            # Format the output nicely for the LLM
            formatted_transactions = "\n".join([
                (f"- Date: {t.get('timestamp', 'N/A').split(' ')[0]}, "
                 f"Amount: {t.get('amount', 'N/A')}, "
                 f"Type: {t.get('payment_type', 'N/A')}, "
                 f"Category: {t.get('category', 'N/A')}, "
                 f"Description: {t.get('message', 'N/A')}")
                for t in response.data
            ])
            return f"Found transactions for user {user_id}:\n{formatted_transactions}"
        else:
            return f"No transactions found for user {user_id} with the specified filters."

    except Exception as e:
        print(f"Error fetching transactions: {e}")
        return "An error occurred while trying to retrieve transactions."
