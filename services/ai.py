from flask import Flask, request, jsonify
from dotenv import load_dotenv
import os
from supabase import create_client, Client  # Replaced Firebase
from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain.tools import Tool
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import HumanMessage, AIMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from datetime import datetime

# --- CONFIGURATION & SETUP ---
load_dotenv()

# 1a. Supabase Initialization (Replaced Firebase)
try:
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_KEY")
    if not supabase_url or not supabase_key:
        raise ValueError("SUPABASE_URL or SUPABASE_KEY environment variables not set.")

    # Use 'db' as variable name to minimize changes
    db: Client = create_client(supabase_url, supabase_key)
    print("--- Supabase Initialized Successfully ---")
except Exception as e:
    print(f"Supabase initialization failed: {e}\nPlease ensure your .env file is present and valid.")
    db = None

# 1b. LangChain (Gemini) Initialization
api_key = os.getenv("GOOGLE_API_KEY")
if not api_key:
    raise ValueError("GOOGLE_API_KEY environment variable not set.")

# --- GLOBAL AGENT EXECUTOR ---
agent_executor = None
agent_initialized = False


# --- CUSTOM TOOLS FOR THE AGENT ---

def get_financial_data(user_id: str) -> str:
    """
    Fetches the latest income and expense transactions for a specific user_id from Supabase
    and returns them as a formatted string for the AI to analyze.
    """
    if not db:
        return "Error: Supabase is not connected."

    print(f"--- TOOL: Fetching financial data for UserID: {user_id} ---")

    try:
        # Fetch latest 25 income transactions
        # *** ASSUMPTION: 'payment_type' is 'income' for income ***
        income_res = db.table('transaction').select('*') \
            .eq('user_id', user_id) \
            .eq('payment_type', 'income') \
            .order('created_at', desc=True) \
            .limit(25).execute()
        income_list = income_res.data

        # Fetch latest 25 expense transactions
        # *** ASSUMPTION: 'payment_type' is 'expense' for expenses ***
        expenses_res = db.table('transaction').select('*') \
            .eq('user_id', user_id) \
            .eq('payment_type', 'expense') \
            .order('created_at', desc=True) \
            .limit(25).execute()
        expenses_list = expenses_res.data

        if not income_list and not expenses_list:
            return "No transaction data found for this user."

        # Format the data into a readable string for the LLM
        response_str = "Here is the user's recent financial data:\n"

        if income_list:
            response_str += "\n--- Recent Income ---\n"
            for item in income_list:
                # Using 'sender_name' and 'created_at' from your schema
                response_str += f"- Amount: {item.get('amount')}, From: {item.get('sender_name')}, Date: {item.get('created_at')}\n"

        if expenses_list:
            response_str += "\n--- Recent Expenses ---\n"
            for item in expenses_list:
                # Using 'sender_name' and 'created_at' from your schema
                response_str += f"- Amount: {item.get('amount')}, To: {item.get('sender_name')}, Date: {item.get('created_at')}\n"

        return response_str

    except Exception as e:
        print(f"Error fetching data from Supabase: {e}")
        return f"An error occurred while fetching financial data: {e}"


# --- AGENT INITIALIZATION ---

def initialize_agent():
    """
    Initializes the language model, tools, and agent executor.
    Runs only once when the application first starts.
    """
    global agent_executor, agent_initialized
    if agent_initialized:
        return

    print("--- Initializing Financial Agent ---")

    # 1. Initialize LLM
    llm = ChatGoogleGenerativeAI(model="gemini-1.0-pro", temperature=0.3)

    # 2. Create Tools
    financial_tool = Tool(
        name="financial_data_retriever",
        func=get_financial_data,
        description="""
        Use this tool to search the user's financial records in Supabase to answer questions about their income, expenses, and spending patterns.
        This tool requires the 'user_id' as an argument.
        """
    )
    tools = [financial_tool]

    # 3. Create Prompt
    prompt = ChatPromptTemplate.from_messages(
        [
            ("system",
             "You are a friendly and helpful AI Financial Assistant. Your primary goal is to answer questions about the user's spending and income by analyzing their transaction data. "
             "You MUST use the 'financial_data_retriever' tool to get the user's transaction history. The user's ID is provided with each request. "
             "Do NOT answer questions about their personal finances from your own general knowledge. If the tool returns no data, inform the user that you couldn't find any transactions for them."),
            ("placeholder", "{chat_history}"),
            ("human", "{input}\n\nUser ID: {user_id}"),  # Pass user_id directly in the prompt
            ("placeholder", "{agent_scratchpad}"),
        ]
    )

    # 4. Create and Assign Agent Executor
    agent = create_tool_calling_agent(llm, tools, prompt)
    agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True)
    agent_initialized = True
    print("--- Financial Agent Initialized Successfully ---")


# --- CHAT HISTORY MANAGEMENT ---

def get_chat_history(user_id: str):
    """Fetches chat history from the 'chat_history' table in Supabase."""
    if not db: return []
    try:
        response = db.table("chat_history").select("chat_history").eq("user_id", user_id).execute()
        if response.data:
            # Your schema has 'chat_history' as the json column
            return response.data[0].get('chat_history', [])
        return []
    except Exception as e:
        print(f"Error getting chat history: {e}")
        return []


def update_chat_history(user_id: str, query: str, response: str):
    """Updates chat history in the 'chat_history' table in Supabase."""
    if not db: return
    try:
        history = get_chat_history(user_id)
        history.append({"human": query, "ai": response})
        history = history[-20:]  # Keep last 20 messages

        # Use upsert to create or update the record
        db.table("chat_history").upsert({
            "user_id": user_id,
            "chat_history": history
        }).execute()
    except Exception as e:
        print(f"Error updating chat history: {e}")


# --- FLASK APPLICATION ---
app = Flask(__name__)


@app.route('/chat', methods=['POST'])
def handle_chat():
    """
    Main endpoint to handle user queries for the financial chatbot.
    Expects JSON: {"UserID", "query"}
    """
    initialize_agent()  # Ensure agent is ready on first request

    if not agent_executor:
        return jsonify({"error": "AI agent is not available."}), 500

    data = request.get_json()
    if not data or "UserID" not in data or "query" not in data:
        return jsonify({"error": "Missing 'UserID' or 'query' in request body"}), 400

    user_id = data["UserID"]
    query = data["query"]

    raw_history = get_chat_history(user_id)
    chat_history = []
    for record in raw_history:
        if record.get("human"): chat_history.append(HumanMessage(content=record["human"]))
        if record.get("ai"): chat_history.append(AIMessage(content=record["ai"]))

    try:
        # Invoke the agent, passing the user_id for the tool to use
        response = agent_executor.invoke({"input": query, "chat_history": chat_history, "user_id": user_id})
        ai_response = response["output"]

        update_chat_history(user_id, query, ai_response)

        return jsonify({"response": ai_response})
    except Exception as e:
        print(f"An error occurred during agent execution: {e}")
        return jsonify({"error": "An error occurred while processing your request."}), 500


if __name__ == '__main__':
    app.run(debug=True, port=5002)  # Running on port 5002 to avoid other services