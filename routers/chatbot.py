from fastapi import APIRouter, HTTPException

from services.chatbot import chat
from models.chat import ChatRequest

router = APIRouter()

@router.post("/chat", tags=["Chatbot"])
async def chabot(request: ChatRequest): 
    """
    Endpoint for handling chatbot interactions. The chatbot internally can hold 10 latest chat message.
    Returns only 1 response from the AI.
    """
    try:
        response = chat.handle_chat(user_id=request.user_id, query=request.message)
        return {"ai": response}
    except Exception as e:
        print(f"An error occurred in /chat endpoint: {e}")
        raise HTTPException(status_code=500, detail=f"An internal server error occurred. {e}")