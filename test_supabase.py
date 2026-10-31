import os
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()
SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_KEY')

client = create_client(SUPABASE_URL, SUPABASE_KEY)

try:
    print("Testing read from rmc_users...")
    res = client.table("rmc_users").select("*").execute()
    print("Read SUCCESS:", res.data)
except Exception as e:
    print("Read ERROR:", e)
