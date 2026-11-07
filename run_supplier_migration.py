"""
Auto-run the supplier migration against Supabase using REST API directly.
"""
import os, urllib.request, urllib.error, json

SUPABASE_URL = 'https://gdmijolkdpfkacnljdfo.supabase.co'
SUPABASE_KEY = 'sb_publishable_gS8nPQmJ6qEHxhlKJDo5Aw_J9PVdzGD'

# Try to get service key from env (needed for DDL)
SERVICE_KEY = os.getenv('SUPABASE_SERVICE_KEY', SUPABASE_KEY)

HEADERS = {
    'apikey': SERVICE_KEY,
    'Authorization': f'Bearer {SERVICE_KEY}',
    'Content-Type': 'application/json',
    'Prefer': 'return=representation'
}

def rpc_or_rest(table, method='GET', data=None, params=''):
    url = f"{SUPABASE_URL}/rest/v1/{table}{params}"
    body = json.dumps(data).encode() if data else None
    req = urllib.request.Request(url, data=body, headers=HEADERS, method=method)
    try:
        with urllib.request.urlopen(req) as r:
            return json.loads(r.read()), r.status
    except urllib.error.HTTPError as e:
        return json.loads(e.read()), e.code

# ── Check if suppliers table exists ──────────────────────────────────────
print("=== Checking suppliers table ===")
data, status = rpc_or_rest('suppliers', 'GET', params='?limit=1')
print(f"Status: {status} | Data: {data}")

# ── Check expenses company_name values ────────────────────────────────────
print("\n=== Expense company names ===")
data, status = rpc_or_rest('expenses', 'GET', params='?select=id,company_name,supplier_id,material_type,category&limit=20')
print(f"Status: {status}")
if isinstance(data, list):
    for e in data:
        print(f"  company={e.get('company_name')!r:25} sup_id={e.get('supplier_id')!r:15} mat={e.get('material_type')!r}")
    print(f"  Total shown: {len(data)}")
else:
    print(f"  Error: {data}")

# ── Seed suppliers ────────────────────────────────────────────────────────
print("\n=== Seeding suppliers ===")
suppliers = [
    {'id':'sup-jj',         'company_name':'JJ SUPPLIER',     'materials_supplied':'M-Sand,Jelly 20mm,Jelly 12mm,Dust', 'gst_no':'', 'phone':'9940270304', 'address':'', 'created_by':'admin'},
    {'id':'sup-uyali',      'company_name':'UYALIAMMAN',      'materials_supplied':'M-Sand,Jelly 20mm,Jelly 12mm,Dust', 'gst_no':'', 'phone':'', 'address':'', 'created_by':'admin'},
    {'id':'sup-murugan',    'company_name':'MURUGAN',         'materials_supplied':'M-Sand,Jelly 20mm,Jelly 12mm,Dust', 'gst_no':'', 'phone':'', 'address':'', 'created_by':'admin'},
    {'id':'sup-ganapathy',  'company_name':'GANAPATHY',       'materials_supplied':'Cement,Chemical',                  'gst_no':'', 'phone':'', 'address':'', 'created_by':'admin'},
    {'id':'sup-nsr',        'company_name':'NSR',             'materials_supplied':'Jelly 20mm,M-Sand,Dust',           'gst_no':'', 'phone':'', 'address':'', 'created_by':'admin'},
    {'id':'sup-smurugan',   'company_name':'SETHUR MURUGAN',  'materials_supplied':'Cement',                           'gst_no':'', 'phone':'', 'address':'', 'created_by':'admin'},
    {'id':'sup-bhagavathi', 'company_name':'BHAGAVATHI',      'materials_supplied':'M-Sand,Jelly 20mm,Jelly 12mm,Dust','gst_no':'', 'phone':'', 'address':'', 'created_by':'admin'},
]

h2 = dict(HEADERS)
h2['Prefer'] = 'resolution=ignore-duplicates,return=minimal'
for s in suppliers:
    url = f"{SUPABASE_URL}/rest/v1/suppliers"
    body = json.dumps(s).encode()
    req = urllib.request.Request(url, data=body, headers=h2, method='POST')
    try:
        with urllib.request.urlopen(req) as r:
            print(f"  Seeded: {s['company_name']} ({r.status})")
    except urllib.error.HTTPError as e:
        err = e.read()
        print(f"  Error seeding {s['company_name']}: {e.code} {err[:200]}")

print("\nDone!")
