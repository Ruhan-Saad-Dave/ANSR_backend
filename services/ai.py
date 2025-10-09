from flask import Flask, request, jsonify
from dotenv import load_dotenv
import os
import firebase_admin
from firebase_admin import credentials, firestore
from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain.tools import Tool
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import HumanMessage, AIMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from datetime import datetime

# --- CONFIGURATION & SETUP ---
load_dotenv()

# 1a. Firebase Initialization
try:
    # IMPORTANT: Replace with your actual service account key filename
    cred = credentials.Certificate("ansr-7f506-firebase-adminsdk-fbsvc-052e7ed895.json")
    firebase_admin.initialize_app(cred)
    db = firestore.client()
    print("--- Firebase Initialized Successfully ---")
except Exception as e:
    print(f"Firebase initialization failed: {e}\nPlease ensure your service account key file is present and valid.")
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
    Fetches the latest income and expense transactions for a specific user_id from Firestore
    and returns them as a formatted string for the AI to analyze.
    """
    if not db:
        return "Error: Firestore is not connected."

    print(f"--- TOOL: Fetching financial data for UserID: {user_id} ---")

    try:
        # Fetch latest 25 income transactions
        income_ref = db.collection('Income').document(user_id).collection('transactions').order_by('timestamp',
                                                                                                   direction=firestore.Query.DESCENDING).limit(
            25).stream()
        income_list = [doc.to_dict() for doc in income_ref]

        # Fetch latest 25 expense transactions
        expenses_ref = db.collection('Expenses').document(user_id).collection('transactions').order_by('timestamp',
                                                                                                       direction=firestore.Query.DESCENDING).limit(
            25).stream()
        expenses_list = [doc.to_dict() for doc in expenses_ref]

        if not income_list and not expenses_list:
            return "No transaction data found for this user."

        # Format the data into a readable string for the LLM
        response_str = "Here is the user's recent financial data:\n"

        if income_list:
            response_str += "\n--- Recent Income ---\n"
            for item in income_list:
                details = item.get('details', {})
                response_str += f"- Amount: {details.get('amount')}, From: {details.get('vendor')}, Date: {item.get('timestamp')}\n"

        if expenses_list:
            response_str += "\n--- Recent Expenses ---\n"
            for item in expenses_list:
                details = item.get('details', {})
                response_str += f"- Amount: {details.get('amount')}, To: {details.get('vendor')}, Date: {item.get('timestamp')}\n"

        return response_str

    except Exception as e:
        print(f"Error fetching data from Firestore: {e}")
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
        Use this tool to search the user's financial records in Firestore to answer questions about their income, expenses, and spending patterns.
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
    if not db: return []
    try:
        doc_ref = db.collection("Chat history").document(user_id).get()
        if doc_ref.exists:
            return doc_ref.to_dict().get('history', [])
        return []
    except Exception as e:
        print(f"Error getting chat history: {e}")
        return []


def update_chat_history(user_id: str, query: str, response: str):
    if not db: return
    try:
        doc_ref = db.collection("Chat history").document(user_id)
        history = get_chat_history(user_id)

        history.append({"human": query, "ai": response})

        # Keep only the last 20 messages (10 pairs of human/ai)
        history = history[-20:]

        doc_ref.set({"history": history}, merge=True)
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
