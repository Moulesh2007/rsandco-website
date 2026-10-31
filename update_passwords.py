import os
from dotenv import load_dotenv
from supabase import create_client
from werkzeug.security import generate_password_hash

load_dotenv()
client = create_client(os.getenv('SUPABASE_URL'), os.getenv('SUPABASE_KEY'))

users = client.table("rmc_users").select("*").execute().data

for user in users:
    # If the password hash does not look like a hash (doesn't start with scrypt or pbkdf2)
    if not str(user.get('password_hash')).startswith('scrypt') and not str(user.get('password_hash')).startswith('pbkdf2'):
        print(f"Updating plain text password for {user['username']}")
        new_hash = generate_password_hash(user['password_hash'])
        client.table("rmc_users").update({"password_hash": new_hash}).eq("id", user["id"]).execute()
        print(f"Success for {user['username']}")
    else:
        print(f"User {user['username']} already has a valid hash.")
