import os
from dotenv import load_dotenv
from supabase import create_client
from werkzeug.security import check_password_hash, generate_password_hash

load_dotenv()
SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_KEY')

client = create_client(SUPABASE_URL, SUPABASE_KEY)

try:
    username_or_email = 'admin'
    password = 'admin123'
    
    print("Testing DB connection...")
    response = client.table("rmc_users").select("*").or_(f"username.eq.{username_or_email},email.eq.{username_or_email}").execute()
    
    if not response.data:
        print("ERROR: User not found in Supabase")
    else:
        user = response.data[0]
        print(f"Found user: {user['username']}")
        print(f"DB Hash: {user['password_hash']}")
        
        is_valid = check_password_hash(user['password_hash'], password)
        print(f"Password Check Result: {is_valid}")
        
        if not is_valid:
            print(f"Valid hash for admin123 would look like: {generate_password_hash(password)}")
except Exception as e:
    print(f"ERROR: {e}")
