"""Fix: Add missing columns to Supabase expenses table via REST API."""
import urllib.request, urllib.error, json

SUPABASE_URL = 'https://gdmijolkdpfkacnljdfo.supabase.co'
SUPABASE_KEY = 'sb_publishable_gS8nPQmJ6qEHxhlKJDo5Aw_J9PVdzGD'

HEADERS = {
    'apikey': SUPABASE_KEY,
    'Authorization': f'Bearer {SUPABASE_KEY}',
    'Content-Type': 'application/json',
}

# 1. Check what columns expenses actually has
print("=== Checking expenses table columns ===")
url = f"{SUPABASE_URL}/rest/v1/expenses?limit=1"
req = urllib.request.Request(url, headers=HEADERS)
try:
    with urllib.request.urlopen(req) as r:
        data = json.loads(r.read())
        if data:
            print("Existing columns:", list(data[0].keys()))
        else:
            print("Table exists but empty - checking via head request")
except urllib.error.HTTPError as e:
    err = json.loads(e.read())
    print(f"Error: {err}")

# 2. Try fetching with select=* to see all columns
print("\n=== All expenses columns (select=*) ===")
url = f"{SUPABASE_URL}/rest/v1/expenses?select=*&limit=2"
req = urllib.request.Request(url, headers=HEADERS)
try:
    with urllib.request.urlopen(req) as r:
        data = json.loads(r.read())
        if data:
            for rec in data:
                print("Columns:", sorted(rec.keys()))
                print("Sample:", {k: rec[k] for k in ['id','category','date'] if k in rec})
                break
        else:
            print("No records found")
except urllib.error.HTTPError as e:
    err = json.loads(e.read())
    print(f"Error: {err}")

# 3. Check if supplier_id column exists  
print("\n=== Checking for supplier_id column ===")
url = f"{SUPABASE_URL}/rest/v1/expenses?select=supplier_id&limit=1"
req = urllib.request.Request(url, headers=HEADERS)
try:
    with urllib.request.urlopen(req) as r:
        print("supplier_id column EXISTS")
except urllib.error.HTTPError as e:
    err = json.loads(e.read())
    print(f"supplier_id column MISSING: {err.get('message')}")

# 4. Check suppliers table columns
print("\n=== Suppliers in Supabase ===")
url = f"{SUPABASE_URL}/rest/v1/suppliers?select=*&limit=20"
req = urllib.request.Request(url, headers=HEADERS)
try:
    with urllib.request.urlopen(req) as r:
        data = json.loads(r.read())
        print(f"Total suppliers: {len(data)}")
        for s in data:
            print(f"  {s.get('id'):20} | {s.get('company_name'):20} | {s.get('materials_supplied')}")
except urllib.error.HTTPError as e:
    print(f"Error: {json.loads(e.read())}")
