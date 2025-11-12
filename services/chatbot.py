import os
from dotenv import load_dotenv
from supabase import create_client, Client
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from core.setup import initialize_firebase
# --- 1. Supabase Initialization ---
# This replaces the get_firestore_client() service
load_dotenv()
db = initialize_firebase



def get_chatbot_response(user_id: str, message: str):
    """
    Handles the chatbot conversation logic using Supabase for chat history.
    """
    if not db:
        return "Error: Supabase client is not initialized. Please check credentials."

    llm = ChatGoogleGenerativeAI(model="gemini-pro", google_api_key=os.getenv("GEMINI_API_KEY"))

    # --- Fetch Chat History from Supabase ---
    # This replaces the Firebase get() logic
    try:
        response = db.table("chat_history").select("chat_history").eq("user_id", user_id).execute()
        if response.data:
            # 'chat_history' is the JSON column in your Supabase schema
            messages_dict = response.data[0].get("chat_history", [])
        else:
            messages_dict = []
    except Exception as e:
        print(f"Error fetching chat history from Supabase: {e}")
        messages_dict = []

    # Convert list of dicts to LangChain message objects
    messages = []
    for msg in messages_dict:
        if msg['role'] == 'user':
            messages.append(HumanMessage(content=msg['content']))
        elif msg['role'] == 'assistant':
            messages.append(AIMessage(content=msg['content']))

    # --- Core LangChain Logic (Unchanged) ---

    # Add the new user message to the history
    messages.append(HumanMessage(content=message))

    # Construct the prompt for Gemini
    prompt = [
        SystemMessage(content="""You are FinSight, a friendly and intelligent financial assistant. Your purpose is to help users understand their spending and make smarter financial decisions. You can answer questions about the user's transactions, subscriptions, budgets, and spending patterns. You can also provide insights and predictions based on their financial activity.

You have access to the following information about the user's financial data:

**Transactions:**
* Amount, date, and time
* Sender/merchant name
* Payment method (Credit, Debit, UPI)
* Category (e.g., Food, Travel)
* Anomalous transaction flags

**Budgets and Limits:**
* Daily, weekly, monthly, and yearly spending limits

**Pending Payments:**
* Money to give or take from others

**Summaries:**
* Daily, weekly, monthly, and yearly income, expenses, and cash flow

**App Features:**
* Subscription and regular payment detection
* Smart alerts and fraud anomaly detection
* Refund and income tracking
* Bill and cashflow prediction
* Spending summaries
* Pending payments tracking

**Your role is to answer questions and provide guidance related to these features and data. If a user asks a question that is not related to their finances or the FinSight app, you must politely decline and steer the conversation back to your purpose. For example, if they ask about the weather or a movie, you should say something like: 'I am a financial assistant and can only answer questions about your finances and the FinSight app. How can I help you with your spending today?'"""),
    ]
    prompt.extend(messages)

    response = llm.invoke(prompt)

    # Add the bot's response to the history
    messages.append(response)

    # --- End of Core Logic ---

    # --- Save Updated Chat History to Supabase ---
    # This replaces the Firebase set() logic

    # Convert LangChain objects back to a list of dicts
    messages_to_save = []
    for msg in messages:
        if isinstance(msg, HumanMessage):
            messages_to_save.append({"role": "user", "content": msg.content})
        elif isinstance(msg, AIMessage):
            messages_to_save.append({"role": "assistant", "content": msg.content})

    # Keep only the last 20 messages (10 pairs)
    messages_to_save = messages_to_save[-20:]

    try:
        # Use upsert to create or update the record for this user_id
        db.table("chat_history").upsert({
            "user_id": user_id,
            "chat_history": messages_to_save  # Store the list in the 'chat_history' JSON column
        }).execute()
    except Exception as e:
        print(f"Error saving chat history to Supabase: {e}")
        # Note: We still return the response even if saving fails

    return response.content