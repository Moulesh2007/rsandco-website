"""
Update existing Supabase expense records:
- Set supplier_name based on description field matching supplier names
- Set supplier_id to the canonical supplier ID
"""
import urllib.request, urllib.error, json, time

SUPABASE_URL = 'https://gdmijolkdpfkacnljdfo.supabase.co'
SUPABASE_KEY = 'sb_publishable_gS8nPQmJ6qEHxhlKJDo5Aw_J9PVdzGD'
H = {'apikey': SUPABASE_KEY, 'Authorization': f'Bearer {SUPABASE_KEY}', 'Content-Type': 'application/json'}

def get(path):
    req = urllib.request.Request(f"{SUPABASE_URL}/rest/v1/{path}", headers=H)
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read())

def patch(table, record_id, data):
    url = f"{SUPABASE_URL}/rest/v1/{table}?id=eq.{record_id}"
    h = dict(H); h['Prefer'] = 'return=minimal'
    req = urllib.request.Request(url, data=json.dumps(data).encode(), headers=h, method='PATCH')
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.status

# Get suppliers - prefer 'sup-*' IDs (our canonical ones)
suppliers_raw = get('suppliers?select=id,company_name')
sup_map = {}  # company_name.upper() -> canonical supplier record
for s in suppliers_raw:
    cn = s['company_name'].strip().upper()
    # Prefer short 'sup-*' IDs
    if cn not in sup_map or s['id'].startswith('sup-'):
        sup_map[cn] = s
print(f"Suppliers loaded: {len(sup_map)}")
for k, v in sup_map.items():
    print(f"  {k} -> {v['id']}")

# Get all expenses
expenses = get('expenses?select=id,description,supplier_id,supplier_name,material_type&limit=500')
print(f"\nExpenses loaded: {len(expenses)}")

updated = 0
skipped = 0
for e in expenses:
    eid = e['id']
    desc = (e.get('description') or '').strip().upper()
    cur_sid = (e.get('supplier_id') or '').strip()
    cur_sname = (e.get('supplier_name') or '').strip().upper()
    
    # Already properly linked?
    if cur_sid and cur_sname:
        skipped += 1
        continue
    
    # Try to find supplier by description
    matched = None
    for cn, s in sup_map.items():
        if cn in desc or desc == cn:
            matched = s
            break
    
    if matched:
        patch_data = {
            'supplier_id': matched['id'],
            'supplier_name': matched['company_name']
        }
        try:
            status = patch('expenses', eid, patch_data)
            print(f"  Updated {eid[:15]} -> {matched['company_name']} (status {status})")
            updated += 1
        except Exception as ex:
            print(f"  Error updating {eid}: {ex}")
    else:
        skipped += 1

print(f"\nDone! Updated: {updated}, Skipped: {skipped}")
