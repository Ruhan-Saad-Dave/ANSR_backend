from core.setup import initialize_firebase

DB = initialize_firebase()

def _get_limit_and_sum(db, user_id, limit_field, sum_field, sum_collection='summary'):
    """Helper function to safely get limit and sum values from Firestore."""
    limit = 0
    total_sum = 0

    try:
        # Safely get the limit value
        limit_doc_ref = db.collection("Limit Table").document(user_id)
        limit_doc = limit_doc_ref.get()
        if limit_doc.exists:
            limit = limit_doc.to_dict().get(limit_field, 0)

        # Safely get the sum value
        sum_doc_ref = db.collection(sum_collection).document(user_id)
        sum_doc = sum_doc_ref.get()
        if sum_doc.exists:
            total_sum = sum_doc.to_dict().get(sum_field, 0)

        # Ensure we are working with numbers, default to 0 if not
        if not isinstance(limit, (int, float)):
            limit = 0
        if not isinstance(total_sum, (int, float)):
            total_sum = 0
            
    except Exception as e:
        # In case of any unexpected Firestore error, return 0 to be safe
        print(f"Error fetching limit/sum for user {user_id}: {e}")
        return 0, 0

    return limit, total_sum

def limit_checker(id):
    db = DB
    alert_msg = ""

    # Daily
    daily_limit, daily_sum = _get_limit_and_sum(db, id, "Daily Limit", "date_sum")
    if daily_limit > 0 and daily_sum >= daily_limit:
        alert_msg += f"Daily limit exceeded\n"
    elif daily_limit > 0 and daily_sum >= 0.8 * daily_limit:
        alert_msg += f"80% of daily limit reached\n"
    elif daily_limit > 0 and daily_sum >= 0.5 * daily_limit:
        alert_msg += f"50% of daily limit reached\n"

    # Weekly
    weekly_limit, weekly_sum = _get_limit_and_sum(db, id, "Weekly limit", "week_sum")
    if weekly_limit > 0 and weekly_sum >= weekly_limit:
        alert_msg += f"Weekly limit exceeded\n"
    elif weekly_limit > 0 and weekly_sum >= 0.8 * weekly_limit:
        alert_msg += f"80% of weekly limit reached\n"
    elif weekly_limit > 0 and weekly_sum >= 0.5 * weekly_limit:
        alert_msg += f"50% of weekly limit reached\n"

    # Monthly
    monthly_limit, monthly_sum = _get_limit_and_sum(db, id, "Monthly limit", "month_sum")
    if monthly_limit > 0 and monthly_sum >= monthly_limit:
        alert_msg += f"Monthly limit exceeded\n"
    elif monthly_limit > 0 and monthly_sum >= 0.8 * monthly_limit:
        alert_msg += f"80% of monthly limit reached\n"
    elif monthly_limit > 0 and monthly_sum >= 0.5 * monthly_limit:
        alert_msg += f"50% of monthly limit reached\n"

    # Yearly
    yearly_limit, yearly_sum = _get_limit_and_sum(db, id, "Yearly limit", "year_sum")
    if yearly_limit > 0 and yearly_sum >= yearly_limit:
        alert_msg += f"Yearly limit exceeded\n"
    elif yearly_limit > 0 and yearly_sum >= 0.8 * yearly_limit:
        alert_msg += f"80% of yearly limit reached\n"
    elif yearly_limit > 0 and yearly_sum >= 0.5 * yearly_limit:
        alert_msg += f"50% of yearly limit reached\n"

    if alert_msg == "":
        return "No alerts"
    return alert_msg.strip()