"""
Final step: Create missing suppliers and link remaining unlinked raw material expenses.
Identified suppliers from unlinked records:
- SST SATHISH (3 M-Sand records)
- JK SUPPLIER / JK SUPPIER (3 Jelly Stones records - normalize to JK SUPPLIER)
- THIRUMALI SUPPLIER / THIRUMALI SUPPIER (1 Jelly Stones record)
- MURUGAR SUPPLIER -> link to MURUGAN (typo)
- CBS CHEMICALS (1 Aggregate record)
"""
import urllib.request, urllib.error, json, time, uuid

SUPABASE_URL = 'https://gdmijolkdpfkacnljdfo.supabase.co'
SUPABASE_KEY = 'sb_publishable_gS8nPQmJ6qEHxhlKJDo5Aw_J9PVdzGD'
H = {'apikey': SUPABASE_KEY, 'Authorization': f'Bearer {SUPABASE_KEY}', 'Content-Type': 'application/json'}

def get(path):
    req = urllib.request.Request(f"{SUPABASE_URL}/rest/v1/{path}", headers=H)
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read())

def post(table, data):
    h = dict(H); h['Prefer'] = 'return=representation'
    req = urllib.request.Request(f"{SUPABASE_URL}/rest/v1/{table}",
                                  data=json.dumps(data).encode(), headers=h, method='POST')
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read()), r.status

def patch(table, field, value, data):
    url = f"{SUPABASE_URL}/rest/v1/{table}?{field}=eq.{urllib.parse.quote(value)}"
    h = dict(H); h['Prefer'] = 'return=minimal'
    req = urllib.request.Request(url, data=json.dumps(data).encode(), headers=h, method='PATCH')
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.status

import urllib.parse

# ── 1. New suppliers to create ────────────────────────────────────────────
NEW_SUPPLIERS = [
    {'id': 'sup-sst',       'company_name': 'SST SATHISH',       'materials_supplied': 'M-Sand'},
    {'id': 'sup-jk',        'company_name': 'JK SUPPLIER',        'materials_supplied': 'Jelly 20mm,Jelly 12mm'},
    {'id': 'sup-thirumali', 'company_name': 'THIRUMALI SUPPLIER', 'materials_supplied': 'Jelly 20mm,Jelly 12mm'},
    {'id': 'sup-cbs',       'company_name': 'CBS CHEMICALS',      'materials_supplied': 'Chemical'},
]

print("=== Creating new suppliers ===")
for s in NEW_SUPPLIERS:
    s['gst_no'] = ''; s['phone'] = ''; s['address'] = ''; s['created_by'] = 'admin'
    try:
        h = dict(H); h['Prefer'] = 'resolution=ignore-duplicates,return=minimal'
        req = urllib.request.Request(f"{SUPABASE_URL}/rest/v1/suppliers",
                                      data=json.dumps(s).encode(), headers=h, method='POST')
        with urllib.request.urlopen(req, timeout=30) as r:
            print(f"  Created: {s['company_name']} (sup id={s['id']}, status={r.status})")
    except urllib.error.HTTPError as ex:
        print(f"  Error creating {s['company_name']}: {ex.read()}")
    time.sleep(0.1)

# ── 2. Description-to-supplier mapping (including typos) ─────────────────
# Maps description patterns -> (supplier_id, canonical_name)
DESC_MAP = {
    'SST SATHISH':         ('sup-sst',       'SST SATHISH'),
    'JK SUPPLIER':         ('sup-jk',        'JK SUPPLIER'),
    'JK SUPPIER':          ('sup-jk',        'JK SUPPLIER'),    # typo
    'THIRUMALI SUPPLIER':  ('sup-thirumali', 'THIRUMALI SUPPLIER'),
    'THIRUMALI SUPPIER':   ('sup-thirumali', 'THIRUMALI SUPPLIER'),  # typo
    'MURUGAR SUPPLIER':    ('sup-murugan',   'MURUGAN'),         # typo -> MURUGAN
    'CBS CHEMICALS':       ('sup-cbs',       'CBS CHEMICALS'),
}

# ── 3. Load all expenses and link unlinked raw material ones ──────────────
print("\n=== Linking unlinked raw material expenses ===")
all_exp = get('expenses?select=id,category,description,supplier_id,supplier_name&limit=500')
unlinked_rm = [
    e for e in all_exp
    if e.get('category') == 'Raw Material'
    and not (e.get('supplier_id') or '').strip()
]
print(f"Unlinked Raw Material expenses: {len(unlinked_rm)}")

updated = 0
no_match = 0
for e in unlinked_rm:
    desc = (e.get('description') or '').strip().upper()
    match = DESC_MAP.get(desc)
    if match:
        sup_id, sup_name = match
        url = f"{SUPABASE_URL}/rest/v1/expenses?id=eq.{e['id']}"
        h2 = dict(H); h2['Prefer'] = 'return=minimal'
        payload = {'supplier_id': sup_id, 'supplier_name': sup_name}
        req = urllib.request.Request(url, data=json.dumps(payload).encode(), headers=h2, method='PATCH')
        try:
            with urllib.request.urlopen(req, timeout=30) as r:
                print(f"  Linked {e['id'][:15]} desc={desc!r} -> {sup_name}")
                updated += 1
        except Exception as ex:
            print(f"  Error: {ex}")
    else:
        print(f"  No match: {e['id'][:15]} desc={desc!r}")
        no_match += 1
    time.sleep(0.05)

print(f"\nUpdated: {updated}, No match: {no_match}")

# ── 4. Final summary ──────────────────────────────────────────────────────
print("\n=== FINAL SUPPLIER EXPENSE COUNTS ===")
time.sleep(1)
all_sups = get('suppliers?select=id,company_name,materials_supplied')
for s in sorted(all_sups, key=lambda x: x['company_name']):
    exps = get(f"expenses?select=id&supplier_id=eq.{s['id']}&limit=500")
    print(f"  {s['company_name']:25} | {s['id']:20} | {len(exps):3} expenses | {s.get('materials_supplied','')}")
