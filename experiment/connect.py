import os
from dotenv import load_dotenv
from supabase import create_client, Client

load_dotenv()
url: str = os.getenv("SUPABASE_URL")
key: str = os.getenv("SUPABASE_KEY")
supabase: Client = create_client(url, key)

#insert data
response = (
    supabase.table("limit")
    .insert({"user_id": 1, "daily": 150, "weekly" : 1200, "monthly": 5000, "yearly": 60000})
    .execute()
)
#print(response.data) # shows the inserted data

#fetch data
response = (
    supabase.table("limit")
    .select("*")
    .execute()
)
print(response.data)

#update
response = (
    supabase.table("limit")
    .update({"daily": 180}) #or upsert
    .eq("id", 1)
    .execute()
)

#delete
response = (
    supabase.table("limit")
    .delete()
    .eq("id", 1)
    .execute()
)