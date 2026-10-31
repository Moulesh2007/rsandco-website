import psycopg2
import sys

# Replace brackets in password
conn_str = "postgresql://postgres:Moulesh2007%40@db.gdmijolkdpfkacnljdfo.supabase.co:5432/postgres"

print("Connecting to database...")
try:
    conn = psycopg2.connect(conn_str)
    conn.autocommit = True
    cursor = conn.cursor()
    print("Connected successfully!")
    
    print("Reading schema.sql...")
    with open("schema.sql", "r", encoding="utf-8") as f:
        sql = f.read()
        
    print("Executing schema.sql...")
    cursor.execute(sql)
    print("Schema executed successfully!")
    
    cursor.close()
    conn.close()
except Exception as e:
    print(f"Database error: {e}")
    sys.exit(1)
