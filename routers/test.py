from fastapi import APIRouter, HTTPException
from pydantic import BaseModel  # Assuming TransactionData is a Pydantic model
from datetime import datetime

from models.chat import ChatRequest
from models.limit import Limit
from models.intake import TransactionData

router = APIRouter()

@router.post("/transaction_intake", tags=["test"])
async def process_raw_transaction(data: TransactionData):
    """
    Receives raw transaction data, calls the parsing service,
    and saves the formatted data to the Supabase database.
    """
    # Just return the received data for testing purposes
    return {"message" : "Data receivesd"}

@router.post("/chatbot", tags = ["test"])
async def chatbot(data: ChatRequest):
    """
    Receives a user message and returns a placeholder AI response.
    """
    user_id = data.user_id
    return {"ai" : f"We got your message, {user_id}"}

@router.post("/change_spending_limit", tags=["test"])
async def alert(data: Limit):
    """
    Changes the spending limit of particular time type.
    Includes daily, weekly, monthly, yearly
    """
    limit = data.limit
    limit_type = data.limit_type
    user_id = data.id

    if limit_type in ["daily", "weekly", "monthly", "yearly"]:
        return {"message" : f"Spending Limit set for user {user_id} with limit {limit} and type {limit_type}"}
    else:
        raise HTTPException(status_code=400, detail="Invalid type. Should be one of 'daily', 'weekly', 'monthly', 'yearly'.")