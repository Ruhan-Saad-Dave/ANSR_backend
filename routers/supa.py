from fastapi import APIRouter

from models.supa import *
from core.setup import initialize_supabase

router = APIRouter()
DB = initialize_supabase()

### transaction, limit, chat_history, pending, summary

# read all
@router.get("/read_all/{table_name}")
async def read_all(table_name: str):
    response = (
        DB.table(table_name)
        .select("*")
        .execute()
    )
    return response.data

# read one 
@router.get("/read_one/transaction")
async def read_one_transaction(transaction: TransactionReadOne):
    user_id = transaction.user_id
    transaction_id = transaction.transaction_id
    if (user_id is None) and (transaction_id is None):
        return {"error": "At least one of user_id or transaction_id must be provided."}
    elif (user_id is None):
        response = (
            DB.table("transaction")
            .select("*")
            .eq("transaction_id", transaction_id)
            .execute()
        )
        return response.data
    elif (transaction_id is None):
        response = (
            DB.table("transaction")
            .select("*")
            .eq("user_id", user_id)
            .execute()
        )
        return response.data
    else:
        response = (
            DB.table("transaction")
            .select("*")
            .eq("user_id", user_id)
            .eq("transaction_id", transaction_id)
            .execute()
        )
        return response.data
    
@router.get("/read_one/limit")
async def read_one_limit(limit: LimitReadOne):
    if limit.user_id is None:
        return {"ERROR": "user_id must be provided."}
    user_id = limit.user_id
    response = (
        DB.table("limit")
        .select("*")
        .eq("user_id", user_id)
        .execute()
    )
    return response.data

@router.get("/read_one/pending")
async def read_one_pending(pending: PendingReadOne):
    user_id = pending.user_id
    pending_id = pending.pending_id
    if (user_id is None) and (pending_id is None):
        return {"ERROR": "At least one of user_id or pending_id must be provided."}
    elif (user_id is None):
        response = (
            DB.table("pending")
            .select("*")
            .eq("pending_id", pending_id)
            .execute()
        )
        return response.data
    elif (pending_id is None):
        response = (
            DB.table("pending")
            .select("*")
            .eq("user_id", user_id)
            .execute()
        )
        return response.data
    else:
        response = (
            DB.table("pending")
            .select("*")
            .eq("user_id", user_id)
            .eq("pending_id", pending_id)
            .execute()
        )
        return response.data
    
@router.get("/read_one/summary")
async def read_one_summary(summary: SummaryReadOne):
    if summary.user_id is None:
        return {"ERROR": "user_id must be provided."}
    user_id = summary.user_id
    response = (
        DB.table("summary")
        .select("*")
        .eq("user_id", user_id)
        .execute()
    )
    return response.data

@router.get("/read_one/chat_history")
async def read_one_chat_history(chat_history: ChatHistoryReadOne):
    if chat_history.user_id is None:
        return {"ERROR": "user_id must be provided."}
    user_id = chat_history.user_id
    response = (
        DB.table("chat_history")
        .select("*")
        .eq("user_id", user_id)
        .execute()
    )
    return response.data

# insert


# update


#upsert


# delete


