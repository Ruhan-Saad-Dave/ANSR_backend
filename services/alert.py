def limit_checker(id):
    db = None 
    alert_msg = ""

    #daily 
    daily_limit = db.get_daily_limit(id)
    daily_sum = db.get_daily_sum(id)
    if daily_sum >= daily_limit: 
        alert_msg += f"Daily limit exceeded\n"
    elif daily_sum >= 0.8 * daily_limit:
        alert_msg += f"80% of daily limit reached\n"
    elif daily_sum >= 0.5 * daily_limit:
        alert_msg += f"50% of daily limit reached\n"
    
    #weekly
    daily_limit = db.get_daily_limit(id)
    daily_sum = db.get_daily_sum(id)
    if daily_sum >= daily_limit: 
        alert_msg += f"Daily limit exceeded\n"
    elif daily_sum >= 0.8 * daily_limit:
        alert_msg += f"80% of daily limit reached\n"
    elif daily_sum >= 0.5 * daily_limit:
        alert_msg += f"50% of daily limit reached\n"

    #monthly
        daily_limit = db.get_daily_limit(id)
    daily_sum = db.get_daily_sum(id)
    if daily_sum >= daily_limit: 
        alert_msg += f"Daily limit exceeded\n"
    elif daily_sum >= 0.8 * daily_limit:
        alert_msg += f"80% of daily limit reached\n"
    elif daily_sum >= 0.5 * daily_limit:
        alert_msg += f"50% of daily limit reached\n"

    #yearly
    daily_limit = db.get_daily_limit(id)
    daily_sum = db.get_daily_sum(id)
    if daily_sum >= daily_limit: 
        alert_msg += f"Daily limit exceeded\n"
    elif daily_sum >= 0.8 * daily_limit:
        alert_msg += f"80% of daily limit reached\n"
    elif daily_sum >= 0.5 * daily_limit:
        alert_msg += f"50% of daily limit reached\n"


    if alert_msg == "":
        return "No alerts"
    return alert_msg