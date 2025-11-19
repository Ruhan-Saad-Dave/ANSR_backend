from fastapi import APIRouter, HTTPException

from services.chatbot import chat  # 1. Corrected import path
from models.chat import ChatRequest

router = APIRouter()

@router.post("/chat")
async def chabot(request: ChatRequest):  # 5. Changed to async for better performance
    try:
        # 2. Fixed argument name from 'message' to 'query'
        response = chat.handle_chat(user_id=request.user_id, query=request.message)
        # 3. Return the response from handle_chat directly
        return response
    except Exception as e:
        # 4. Improved error handling to not leak details
        print(f"An error occurred in /chat endpoint: {e}") # Log error for debugging
        raise HTTPException(status_code=500, detail="An internal server error occurred.")

