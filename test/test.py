import time
import datetime
import requests 

user_id = "test_user_1" # Change it as needed
base = "http://localhost:8000/"

def transaction():
    raw_message = input("Enter the raw message:")
    timestamp = datetime.datetime.now().isoformat()
    data = {
        "user_id": user_id,
        "raw_message": raw_message,
        "timestamp": timestamp
    }
    response = requests.post(base + "transactions/add", json=data)
    print("Server response:", response.json())

def spending():
    spending_type = input("Enter spending type (daily, weekly, monthly, yearly): ")
    if spending_type not in ["daily", "weekly", "monthly", "yearly"]:
        print("Invalid spending type.")
        return
    amount = float(input("Enter new spending limit amount: "))
    data = {
        "user_id": user_id,
        "spending_type": spending_type,
        "amount": amount
    }
    response = requests.post(base + "spending/set_limit", json=data)
    print("Server response:", response.json())

def chatbot():
    while True:
        msg = input("You: ")
        if msg.lower() in ["exit", "quit", "q"]:
            print("Exiting chatbot...\n\n")
            break
        response = requests.post(base + "chatbot/chat", json={"user_id": user_id, "message": msg})
        #print(response.json())

        print("AI:", response.json().get("response"))

def pending():
    pass

def summary():
    data = {
        "user_id": user_id
    }
    response = requests.post(base + "/supa/read_one/summary", json=data)
    print("Summary:", response.json())

# __main__
while True:
    print("1. Send Transaction Data")
    print("2. Change Spending Limit")
    print("3. Chatbot")
    print("4. Set Pending Payment")
    print("5. View Summary")
    print("X. Exit")
    choice = input("Choose an option: ")

    if choice == "1":
        transaction()
    elif choice == "2":
        spending()
    elif choice == "3":
        chatbot()
    elif choice == "4":
        pending()
    elif choice == "5":
        summary()
    else:
        break
print("exiting system...")
