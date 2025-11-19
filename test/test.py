import time
import datetime
import requests 

user_id = "test_user_1"
base = "http://localhost:8000/"

def transaction():
    pass

def spending():
    pass

def chatbot():
    while True:
        msg = input("You: ")
        if msg.lower() in ["exit", "quit", "q"]:
            print("Exiting chatbot...\n\n")
            break
        response = requests.post(base + "chatbot/chat", json={"user_id": user_id, "message": msg})

######################

def pending():
    pass

def summary():
    pass

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
