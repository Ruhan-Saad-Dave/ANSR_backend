from supabase import Client
from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain.tools import Tool
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import HumanMessage, AIMessage
from langchain_google_genai import ChatGoogleGenerativeAI

from core.setup import initialize_supabase
from .tools import get_summary, get_limit, get_pending, get_transactions

db = initialize_supabase()
llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", temperature=0.3)

# 2. Create Tools
summary_tool = Tool(
    name="Summary_Retriever",
    func=get_summary,
    description="""
    Use this tool to get the summary of the user's financial data from supabase.
    It includes income, expense and cashflow per day, week, month and year.
    This tool requires the 'user_id' as an argument.
    """
)

limit_tool = Tool(
    name="Spending_Limit_Retriever",
    func=get_limit,
    description="""
    Use this tool to get the Spending Limit set by the user from supabase.
    It includes spending limit of daily, weekly, monthly and yearly.
    This tool requires the 'user_id' as an argument.
    """
)

pending_tool = Tool(
    name="Pending_Transactions_Retriever",
    func=get_pending,
    description="""
    Use this tool to get the Pending Transactions of the user from supabase.
    It includes the list of pending transactions with other users and the amounts owed or to be received.
    A positive value means the other user owes money, negative for current user owes money.
    This tool requires the 'user_id' as an argument.
    """
)

transaction_tool = Tool(
    name="Transaction_Retriever",
    func=get_transactions,
    description="""
    Use this tool to find and retrieve a user's transactions to answer detailed questions about their spending or income.
    It supports filtering by 'start_date' (YYYY-MM-DD), 'end_date' (YYYY-MM-DD), 'category', and 'payment_type' ('income' or 'expense').
    If no dates are given, it defaults to the last 30 days.
    Always provide the 'user_id'.
    This is the primary tool for any question involving specific transaction details, amounts, categories, or dates.
    """
)

tools = [summary_tool, limit_tool, pending_tool, transaction_tool]

# 3. Create Prompt
prompt = ChatPromptTemplate.from_messages(
    [
        ("system",
         "You are a friendly and helpful AI Financial Assistant. Your primary goal is to answer questions about the user's finances. "
         "To answer, you must use the tools provided to retrieve the necessary financial data. The user's ID is provided with each request. "
         "The available tools are: "
         "- 'Summary_Retriever': For overall financial summaries (income, expense, cashflow). "
         "- 'Spending_Limit_Retriever': For user-defined spending limits. "
         "- 'Pending_Transactions_Retriever': For pending transactions with other users. "
         "- 'Transaction_Retriever': For finding specific transactions by date, category, or type (income/expense). Use this for all detailed questions about spending history. "
         "Do NOT answer questions about their personal finances from your own general knowledge. If a tool returns no data, inform the user that you couldn't find the requested information."),
        ("placeholder", "{chat_history}"),
        ("human", "{input}\n\nUser ID: {user_id}"),  # Pass user_id directly in the prompt
        ("placeholder", "{agent_scratchpad}"),
    ]
)



# 4. Create and Assign Agent Executor
agent = create_tool_calling_agent(llm, tools, prompt)
agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True)


########

def get_chat_history(user_id: str):
    """Fetches chat history from the 'chat_history' table in Supabase."""
    if not db: 
        return []
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
        history = history[-10:]  # Keep last 10 messages

        # Use upsert to create or update the record
        db.table("chat_history").upsert({
            "user_id": user_id,
            "chat_history": history
        }).execute()
    except Exception as e:
        print(f"Error updating chat history: {e}")


def handle_chat(user_id: str, query: str):
    """
    Main endpoint to handle user queries for the financial chatbot.
    Expects JSON: {"UserID", "query"}
    """
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

        return {"response": ai_response}
    except Exception as e:
        return {"error": f"An error occurred during agent execution: {e}"}