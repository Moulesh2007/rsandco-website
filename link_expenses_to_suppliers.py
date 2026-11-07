"""Check actual expense data to understand matching fields."""
import urllib.request, urllib.error, json

SUPABASE_URL = 'https://gdmijolkdpfkacnljdfo.supabase.co'
SUPABASE_KEY = 'sb_publishable_gS8nPQmJ6qEHxhlKJDo5Aw_J9PVdzGD'
HEADERS = {'apikey': SUPABASE_KEY, 'Authorization': f'Bearer {SUPABASE_KEY}', 'Content-Type': 'application/json'}

# 1. Check all expense records
url = f"{SUPABASE_URL}/rest/v1/expenses?select=id,category,date,description,material_type,supplier_id,supplier_name&limit=50"
req = urllib.request.Request(url, headers=HEADERS)
with urllib.request.urlopen(req) as r:
    expenses = json.loads(r.read())
    print(f"Total expenses: {len(expenses)}")
    for e in expenses:
        print(f"  id={e['id'][:15]} | desc={str(e.get('description',''))[:25]:25} | mat={str(e.get('material_type',''))[:15]:15} | sup_id={e.get('supplier_id','')[:15]:15} | sup_name={e.get('supplier_name','')}")

# 2. Get suppliers list
print("\n=== SUPPLIERS ===")
url2 = f"{SUPABASE_URL}/rest/v1/suppliers?select=id,company_name"
req2 = urllib.request.Request(url2, headers=HEADERS)
with urllib.request.urlopen(req2) as r:
    suppliers = json.loads(r.read())
    for s in suppliers:
        print(f"  {s['id']:40} | {s['company_name']}")

# 3. Try to update expenses to link supplier_id/supplier_name
# Only update if description matches a supplier name
print("\n=== Attempting to link expenses to suppliers by description ===")
sup_map = {}
for s in suppliers:
    cn = s['company_name'].upper().strip()
    # Prefer the short IDs
    if cn not in sup_map or s['id'].startswith('sup-'):
        sup_map[cn] = s

for e in expenses:
    desc = (e.get('description') or '').upper().strip()
    if not e.get('supplier_id') and desc in sup_map:
        sup = sup_map[desc]
        patch = {'supplier_id': sup['id'], 'supplier_name': sup['company_name']}
        url3 = f"{SUPABASE_URL}/rest/v1/expenses?id=eq.{e['id']}"
        h3 = dict(HEADERS); h3['Prefer'] = 'return=minimal'
        req3 = urllib.request.Request(url3, data=json.dumps(patch).encode(), headers=h3, method='PATCH')
        try:
            with urllib.request.urlopen(req3) as r:
                print(f"  Linked {e['id']} -> {sup['company_name']}")
        except urllib.error.HTTPError as ex:
            print(f"  Error linking {e['id']}: {ex.read()}")
    elif e.get('supplier_id'):
        print(f"  Already linked: {e['id'][:15]} -> {e.get('supplier_name')}")
    else:
        print(f"  No match for: {e['id'][:15]} desc={desc!r}")
