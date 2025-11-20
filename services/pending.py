#

def clean(data):
    owes = {}
    for entry in data:
        other_user = entry.get("other_user")
        amount = entry.get("amount")

        if not other_user or amount is None:
            continue

        if other_user not in owes:
            owes[other_user] = 0
        
        if entry.get("is_current_debtor"):
            owes[other_user] += amount
        else:
            owes[other_user] -= amount

    final_data = []
    for other_user, amount in owes.items():
        if amount < 0:
            final_data.append({
                "other_user": other_user,
                "amount": -amount,
                "is_current_debtor": False
            })
        elif amount > 0:
            final_data.append({
                "other_user": other_user,
                "amount": amount,
                "is_current_debtor": True
            })
    return final_data
        