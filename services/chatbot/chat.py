import os 
from dotenv import load_dotenv
from supabase import create_client, Client
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage

from core.setup import initialize_supabase

# 1. Initialization
load_dotenv()
db = initialize_supabase()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

def get_chatbot_response(user_id: str, message: str):
    """
    Handles the chatbot conversation logic using Supabase for chat history.
    """
    if not db:
        return "Error: Supabase client is not initialized. Please check credentials."

    llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", google_api_key=GEMINI_API_KEY)

    # 2. Fetch Chat History from Supabase
    try:
        response = db.table("chat_history").select("chat_message").eq("user_id", user_id).execute()
        if response.data:
            messages_dict = response.data[0].get("chat_history", [])
        else:
            messages_dict = []
    except Exception as e:
        return {"message" : f"Error fetching chat history from Supabase: {e}"}
        

    # Convert list of dicts to LangChain message objects
    messages = []
    for msg in messages_dict:
        if msg['role'] == 'user':
            messages.append(HumanMessage(content=msg['content']))
        elif msg['role'] == 'assistant':
            messages.append(AIMessage(content=msg['content']))

    # 3. Core LangChain Logic (Unchanged)

    # Add the new user message to the history
    messages.append(HumanMessage(content=message))

    # Construct the prompt for Gemini
    prompt = [
        SystemMessage(content="""You are FinSight, a friendly and intelligent financial assistant. Your purpose is to help users understand their spending and make smarter financial decisions. You can answer questions about the user's transactions, subscriptions, budgets, and spending patterns. You can also provide insights and predictions based on their financial activity.""")
    ] + messages

    # Get the response from Gemini
    try:
        response = llm.generate_responses(prompt)
        bot_message = response.generations[0][0].text  
    except Exception as e:
        print(f"Error generating response from Gemini: {e}")
        bot_message = "I'm sorry, but I'm currently unable to process your request."
    # Add the bot's response to the history
    messages.append(AIMessage(content=bot_message))
    if len(messages) > 10:
        messages = messages[-10:]  # Keep only the last 10 messages

    # 4. Update Chat History in Supabase
    messages_to_store = [{"role": "user" if isinstance(msg, HumanMessage) else "assistant", "content": msg.content} for msg in messages]   
    try:    
        db.table("chat_history").upsert({
            "user_id": user_id,
            "chat_history": messages_to_store
        }).execute()
    except Exception as e:
        return {"message" : f"Error updating chat history in Supabase: {e}"}
    return bot_message

