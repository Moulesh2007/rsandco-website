import os
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()
SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_KEY')

client = create_client(SUPABASE_URL, SUPABASE_KEY)

tables = ["manual_billing", "expenses", "rmc_users", "rmc_clients", "rmc_orders", "rmc_invoices", "rmc_payments"]

for table in tables:
    try:
        res = client.table(table).select("*").limit(1).execute()
        print(f"READ {table}: OK - rows={len(res.data)}")
    except Exception as e:
        print(f"READ {table}: ERROR - {e}")

# Test insert into manual_billing
import uuid
test_record = {
    "id": f"test-{uuid.uuid4().hex[:8]}",
    "company_name": "Test Co",
    "phone": "9999999999",
    "address": "Test Addr",
    "date": "2026-06-12",
    "time": "10:00",
    "vehicle_number": "TN-01-XX-9999",
    "driver_name": "Test Driver",
    "unloading_time": "10:30",
    "grade": "M25",
    "cubic_meters": "5",
    "loading_time": "09:45",
    "rate_per_cubic": "4500",
    "total_amount": 22500,
    "advance_amount": 0,
    "balance_amount": 22500,
    "created_at": "2026-06-12T10:00:00",
    "created_by": "test"
}
try:
    res = client.table("manual_billing").insert(test_record).execute()
    print(f"\nINSERT manual_billing: OK - {res.data}")
    # Clean up
    client.table("manual_billing").delete().eq("id", test_record["id"]).execute()
    print("Cleanup: deleted test record")
except Exception as e:
    print(f"\nINSERT manual_billing: ERROR - {e}")

# Test insert into expenses
test_expense = {
    "id": f"test-exp-{uuid.uuid4().hex[:8]}",
    "category": "Test",
    "date": "2026-06-12",
    "description": "Test expense",
    "material_type": "",
    "quantity": "",
    "rate_per_ton": "",
    "amount": 1000,
    "total_amount": 1000,
    "advance_amount": 0,
    "balance_amount": 1000,
    "created_at": "2026-06-12T10:00:00",
    "created_by": "test"
}
try:
    res = client.table("expenses").insert(test_expense).execute()
    print(f"\nINSERT expenses: OK - {res.data}")
    client.table("expenses").delete().eq("id", test_expense["id"]).execute()
    print("Cleanup: deleted test expense")
except Exception as e:
    print(f"\nINSERT expenses: ERROR - {e}")
