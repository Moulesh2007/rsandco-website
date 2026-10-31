import os
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()
SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_KEY')

client = create_client(SUPABASE_URL, SUPABASE_KEY)

admin_hash = "scrypt:32768:8:1$SeGsDKf0qXizMboX$b0433b16675a3e209b97cc097b5f66c1fd4ac3a7ef4da22dc3e8aa3bce2ff12b0ecdead95c64f184d5bbd517d30ea502f450cebfbee47683bf595092a4d2c198"
manager_hash = "scrypt:32768:8:1$Gcyo7TWCU4MZ5zxL$997c7a585f3ec8587f3f7375ef1649fd4ba77a23ca46dcafb2805295ed9b9fdf9ee72180e74f0594fd658c89f4b3924c8ae26d9724b3c08b93c95f6d3a42484d"

try:
    print("Updating admin hash...")
    client.table("rmc_users").update({"password_hash": admin_hash}).eq("username", "admin").execute()
    
    print("Updating manager hash...")
    client.table("rmc_users").update({"password_hash": manager_hash}).eq("username", "manager").execute()
    
    print("Update complete!")
except Exception as e:
    print("ERROR:", e)
