from core.setup import initialize_firebase  # Using your custom initializer
from datetime import datetime, timedelta
from collections import defaultdict
import numpy as np
from dateutil.parser import parse as parse_datetime  # For parsing ISO timestamps


def get_spending_prediction(user_id: str, timeframe: str):
    """
    Predicts future expenses based on historical data from Supabase.
    """
    try:
        db = initialize_firebase()
        if not db:
            raise Exception("Supabase client not initialized")

        # Fetch last 90 days of transactions for the user
        ninety_days_ago = (datetime.now() - timedelta(days=90)).isoformat()

        # Query the 'transaction' table
        response = db.table('transaction').select('created_at, amount, payment_type') \
            .eq('user_id', user_id) \
            .gte('created_at', ninety_days_ago) \
            .execute()

        transactions = response.data

        if len(transactions) < 15:
            return {"message": "Not enough data for a reliable prediction."}

        # Separate expenses
        # Map 'outgoing' to 'expense' per your schema
        expenses = [tx for tx in transactions if tx.get('payment_type') == 'expense']

        if not expenses:
            return {"message": "No expense data available for prediction."}

        # Group expenses by day
        daily_expenses = defaultdict(float)
        for expense in expenses:
            # Parse the 'created_at' timestamp string
            expense_date = parse_datetime(expense['created_at']).date()
            daily_expenses[expense_date] += expense['amount']

        if not daily_expenses:
            return {"message": "Not enough daily expense data for prediction."}

        # Calculate average daily expense
        avg_daily_expense = sum(daily_expenses.values()) / len(daily_expenses)

        # Trend calculation
        last_30_days_expenses = [v for k, v in daily_expenses.items() if
                                 k >= (datetime.now() - timedelta(days=30)).date()]
        previous_30_days_expenses = [v for k, v in daily_expenses.items() if
                                     (datetime.now() - timedelta(days=60)).date() <= k < (
                                                 datetime.now() - timedelta(days=30)).date()]

        avg_last_30_days = sum(last_30_days_expenses) / len(last_30_days_expenses) if last_30_days_expenses else 0
        avg_previous_30_days = sum(previous_30_days_expenses) / len(
            previous_30_days_expenses) if previous_30_days_expenses else 0

        if avg_previous_30_days > 0:
            trend = ((avg_last_30_days - avg_previous_30_days) / avg_previous_30_days) * 100
        else:
            trend = 0

        if timeframe == 'daily':
            prediction = avg_daily_expense
        elif timeframe == 'weekly':
            prediction = avg_daily_expense * 7
        elif timeframe == 'monthly':
            prediction = avg_daily_expense * 30
        else:
            return {"message": "Invalid timeframe specified. Use 'daily', 'weekly', or 'monthly'."}

        return {"predicted_expense": round(prediction, 2), "trend": round(trend, 2)}

    except Exception as e:
        print(f"An error occurred: {e}")
        return {"message": "An error occurred during prediction."}


def get_cashflow_prediction(user_id: str, timeframe: str):
    """
    Predicts future cashflow based on historical data from Supabase.
    """
    try:
        db = initialize_firebase()
        if not db:
            raise Exception("Supabase client not initialized")

        # Fetch last 90 days of transactions for the user
        ninety_days_ago = (datetime.now() - timedelta(days=90)).isoformat()

        # Query the 'transaction' table
        response = db.table('transaction').select('created_at, amount, payment_type') \
            .eq('user_id', user_id) \
            .gte('created_at', ninety_days_ago) \
            .execute()

        transactions = response.data

        if len(transactions) < 15:
            return {"message": "Not enough data for a reliable prediction."}

        # Separate expenses and income
        # Map 'outgoing'/'incoming' to 'expense'/'income' per your schema
        expenses = [tx for tx in transactions if tx.get('payment_type') == 'expense']
        income = [tx for tx in transactions if tx.get('payment_type') == 'income']

        if not expenses and not income:
            return {"message": "No transaction data available for prediction."}

        # Group expenses by day
        daily_expenses = defaultdict(float)
        for expense in expenses:
            expense_date = parse_datetime(expense['created_at']).date()
            daily_expenses[expense_date] += expense['amount']

        # Group income by day
        daily_income = defaultdict(float)
        for inc in income:
            income_date = parse_datetime(inc['created_at']).date()
            daily_income[income_date] += inc['amount']

        # Calculate average daily expense and income
        avg_daily_expense = sum(daily_expenses.values()) / len(daily_expenses) if daily_expenses else 0
        avg_daily_income = sum(daily_income.values()) / len(daily_income) if daily_income else 0

        avg_daily_cashflow = avg_daily_income - avg_daily_expense

        if timeframe == 'daily':
            prediction = avg_daily_cashflow
        elif timeframe == 'weekly':
            prediction = avg_daily_cashflow * 7
        elif timeframe == 'monthly':
            prediction = avg_daily_cashflow * 30
        else:
            return {"message": "Invalid timeframe specified. Use 'daily', 'weekly', or 'monthly'."}

        return {"predicted_cashflow": round(prediction, 2)}

    except Exception as e:
        print(f"An error occurred: {e}")
        return {"message": "An error occurred during prediction."}


def get_daily_spending_trend(user_id: str):
    """
    Gets the daily spending trend for the last 7 days from Supabase.
    """
    try:
        db = initialize_firebase()
        if not db:
            raise Exception("Supabase client not initialized")

        # Fetch last 7 days of transactions for the user
        seven_days_ago = (datetime.now() - timedelta(days=7)).isoformat()

        # Query for 'expense' types
        response = db.table('transaction').select('created_at, amount') \
            .eq('user_id', user_id) \
            .gte('created_at', seven_days_ago) \
            .eq('payment_type', 'expense') \
            .execute()

        transactions = response.data

        daily_spending = defaultdict(float)
        for tx in transactions:
            tx_date = parse_datetime(tx['created_at']).date()
            daily_spending[tx_date] += tx['amount']

        # Create a list of the last 7 days
        last_7_days = [(datetime.now() - timedelta(days=i)).date() for i in range(7)]

        trend_data = {day.strftime("%Y-%m-%d"): daily_spending.get(day, 0) for day in sorted(last_7_days)}

        return {"daily_spending_trend": trend_data}

    except Exception as e:
        print(f"An error occurred: {e}")
        return {"message": "An error occurred while fetching daily trend."}


def get_monthly_spending_trend(user_id: str):
    """
    Gets the monthly spending trend for the last 12 months from Supabase.
    """
    try:
        db = initialize_firebase()
        if not db:
            raise Exception("Supabase client not initialized")

        # Fetch last 12 months of transactions for the user
        twelve_months_ago = (datetime.now() - timedelta(days=365)).isoformat()

        # Query for 'expense' types
        response = db.table('transaction').select('created_at, amount') \
            .eq('user_id', user_id) \
            .gte('created_at', twelve_months_ago) \
            .eq('payment_type', 'expense') \
            .execute()

        transactions = response.data

        monthly_spending = defaultdict(float)
        for tx in transactions:
            tx_date = parse_datetime(tx['created_at'])
            monthly_spending[tx_date.strftime("%Y-%m")] += tx['amount']

        # Create a list of the last 12 months (by month string)
        current_date = datetime.now().date()
        last_12_months = []
        for i in range(12):
            # Go back month by month
            month_date = (current_date.replace(day=1) - timedelta(days=i * 30)).replace(day=1)
            last_12_months.append(month_date.strftime("%Y-%m"))

        # Get unique, sorted months
        sorted_unique_months = sorted(list(set(last_12_months)), reverse=True)

        trend_data = {month: monthly_spending.get(month, 0) for month in sorted_unique_months}

        return {"monthly_spending_trend": trend_data}

    except Exception as e:
        print(f"An error occurred: {e}")
        return {"message": "An error occurred while fetching monthly trend."}