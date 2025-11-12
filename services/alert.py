from core.setup import initialize_firebase

db = initialize_firebase()


def limit_checker(user_id):
    # db is assumed to be your global Supabase client
    alert_msg = ""
    limit_data = {}
    sum_data = {}

    try:
        # 1. Fetch all limits for the user in one query
        # We use maybe_single() to safely get one row or None
        limit_res = db.table('limit').select('daily', 'weekly', 'monthly', 'yearly') \
            .eq('user_id', user_id).maybe_single().execute()
        if limit_res.data:
            limit_data = limit_res.data

    except Exception as e:
        print(f"Error fetching limits from Supabase for user {user_id}: {e}")

    try:
        # 2. Fetch all summary expense data for the user in one query
        # We map the old "sum" fields to your new schema's "_out" fields
        sum_res = db.table('summary').select('day_out', 'week_out', 'month_out', 'year_out') \
            .eq('user_id', user_id).maybe_single().execute()
        if sum_res.data:
            sum_data = sum_res.data

    except Exception as e:
        print(f"Error fetching sums from Supabase for user {user_id}: {e}")

    # Helper function to safely get and validate numbers from the fetched data
    def safe_get(data_dict, key):
        val = data_dict.get(key, 0)
        # Ensure we are working with numbers, default to 0 if not
        if not isinstance(val, (int, float)):
            return 0
        return val

    # --- Daily Check ---
    # Maps 'Daily Limit' to 'daily' and 'date_sum' to 'day_out'
    daily_limit = safe_get(limit_data, 'daily')
    daily_sum = safe_get(sum_data, 'day_out')

    if daily_limit > 0 and daily_sum >= daily_limit:
        alert_msg += "Daily limit exceeded\n"
    elif daily_limit > 0 and daily_sum >= 0.8 * daily_limit:
        alert_msg += "80% of daily limit reached\n"
    elif daily_limit > 0 and daily_sum >= 0.5 * daily_limit:
        alert_msg += "50% of daily limit reached\n"

    # --- Weekly Check ---
    # Maps 'Weekly limit' to 'weekly' and 'week_sum' to 'week_out'
    weekly_limit = safe_get(limit_data, 'weekly')
    weekly_sum = safe_get(sum_data, 'week_out')

    if weekly_limit > 0 and weekly_sum >= weekly_limit:
        alert_msg += "Weekly limit exceeded\n"
    elif weekly_limit > 0 and weekly_sum >= 0.8 * weekly_limit:
        alert_msg += "80% of weekly limit reached\n"
    elif weekly_limit > 0 and weekly_sum >= 0.5 * weekly_limit:
        alert_msg += "50% of weekly limit reached\n"

    # --- Monthly Check ---
    # Maps 'Monthly limit' to 'monthly' and 'month_sum' to 'month_out'
    monthly_limit = safe_get(limit_data, 'monthly')
    monthly_sum = safe_get(sum_data, 'month_out')

    if monthly_limit > 0 and monthly_sum >= monthly_limit:
        alert_msg += "Monthly limit exceeded\n"
    elif monthly_limit > 0 and monthly_sum >= 0.8 * monthly_limit:
        alert_msg += "80% of monthly limit reached\n"
    elif monthly_limit > 0 and monthly_sum >= 0.5 * monthly_limit:
        alert_msg += "50% of monthly limit reached\n"

    # --- Yearly Check ---
    # Maps 'Yearly limit' to 'yearly' and 'year_sum' to 'year_out'
    yearly_limit = safe_get(limit_data, 'yearly')
    yearly_sum = safe_get(sum_data, 'year_out')

    if yearly_limit > 0 and yearly_sum >= yearly_limit:
        alert_msg += "Yearly limit exceeded\n"
    elif yearly_limit > 0 and yearly_sum >= 0.8 * yearly_limit:
        alert_msg += "80% of yearly limit reached\n"
    elif yearly_limit > 0 and yearly_sum >= 0.5 * yearly_limit:
        alert_msg += "50% of yearly limit reached\n"

    if alert_msg == "":
        return "No alerts"
    return alert_msg.strip()