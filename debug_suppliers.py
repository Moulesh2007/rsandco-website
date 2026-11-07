import os
os.environ['SUPABASE_URL'] = 'https://gdmijolkdpfkacnljdfo.supabase.co'
os.environ['SUPABASE_KEY'] = 'sb_publishable_gS8nPQmJ6qEHxhlKJDo5Aw_J9PVdzGD'
from supabase import create_client

client = create_client(os.environ['SUPABASE_URL'], os.environ['SUPABASE_KEY'])

# 1. Check suppliers table
print("=== SUPPLIERS TABLE ===")
try:
    resp = client.table('suppliers').select('*').execute()
    print(f"Count: {len(resp.data)}")
    for s in resp.data:
        print(f"  {s.get('company_name')} | id={s.get('id')} | materials={s.get('materials_supplied')}")
except Exception as e:
    print(f"ERROR reading suppliers: {e}")

# 2. Check expenses - what company names are stored?
print("\n=== EXPENSES - COMPANY NAMES ===")
try:
    resp = client.table('expenses').select('id,company_name,supplier_name,supplier_id,material_type,category,date').execute()
    print(f"Total expenses: {len(resp.data)}")
    names = set()
    for e in resp.data:
        cn = e.get('company_name','')
        sn = e.get('supplier_name','')
        sid = e.get('supplier_id','')
        mt = e.get('material_type','')
        cat = e.get('category','')
        names.add(cn)
        print(f"  company='{cn}' | sup_name='{sn}' | sup_id='{sid}' | material='{mt}' | cat='{cat}'")
    print(f"\nUnique company names: {names}")
except Exception as e:
    print(f"ERROR reading expenses: {e}")

# 3. Check if supplier_id column exists
print("\n=== EXPENSE COLUMNS CHECK ===")
try:
    resp = client.table('expenses').select('supplier_id,supplier_name').limit(1).execute()
    print("supplier_id and supplier_name columns EXIST")
except Exception as e:
    print(f"Columns missing: {e}")
