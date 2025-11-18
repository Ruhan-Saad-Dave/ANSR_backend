import os
from dotenv import load_dotenv
from supabase import create_client, Client

load_dotenv()
url: str = os.getenv("SUPABASE_URL")
key: str = os.getenv("SUPABASE_KEY")
supabase: Client = create_client(url, key)

response = (
    supabase.table("chat_history")
    .select("*")
    .eq("user_id", 1)
    .execute()
)
if(len(response.data) > 0):
    print(response.data)
