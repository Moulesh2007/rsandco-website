"""
Complete the supplier migration:
1. Retry the 2 failed expense updates
2. Check what the 99 skipped records are
3. Remove duplicate suppliers (keep sup-* IDs, delete UUID ones)
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

def delete(table, record_id):
    url = f"{SUPABASE_URL}/rest/v1/{table}?id=eq.{record_id}"
    req = urllib.request.Request(url, headers=H, method='DELETE')
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.status

# ── 1. Get suppliers, build map ───────────────────────────────────────────
suppliers_raw = get('suppliers?select=id,company_name,materials_supplied,phone,gst_no')
print(f"=== All suppliers ({len(suppliers_raw)}) ===")
for s in suppliers_raw:
    print(f"  {s['id']:40} | {s['company_name']}")

# Preferred IDs: sup-* wins over UUID
sup_map = {}
uuid_dups = []
for s in suppliers_raw:
    cn = s['company_name'].strip().upper()
    if s['id'].startswith('sup-'):
        sup_map[cn] = s
    else:
        uuid_dups.append(s)

# ── 2. Migrate expenses from UUID supplier_id to sup-* supplier_id ────────
print("\n=== Migrating UUID supplier_ids to canonical sup-* ids ===")
for dup in uuid_dups:
    cn = dup['company_name'].strip().upper()
    if cn in sup_map:
        canonical = sup_map[cn]
        # Find expenses that point to this UUID supplier
        exps = get(f"expenses?select=id,supplier_id&supplier_id=eq.{dup['id']}&limit=500")
        print(f"  {dup['id'][:36]} ({dup['company_name']}) -> {canonical['id']}: {len(exps)} expenses to remap")
        for e in exps:
            try:
                patch('expenses', e['id'], {'supplier_id': canonical['id'], 'supplier_name': canonical['company_name']})
            except Exception as ex:
                print(f"    Error remapping {e['id']}: {ex}")
        time.sleep(0.1)

# ── 3. Delete duplicate UUID suppliers ───────────────────────────────────
print("\n=== Deleting duplicate UUID suppliers ===")
for dup in uuid_dups:
    cn = dup['company_name'].strip().upper()
    if cn in sup_map:
        try:
            status = delete('suppliers', dup['id'])
            print(f"  Deleted {dup['id']} ({dup['company_name']}) - status {status}")
        except Exception as ex:
            print(f"  Error deleting {dup['id']}: {ex}")
        time.sleep(0.1)

# ── 4. Check unlinked expenses ────────────────────────────────────────────
print("\n=== Unlinked expenses (no supplier_id or supplier_name) ===")
all_exp = get('expenses?select=id,category,description,material_type,supplier_id,supplier_name&limit=500')
unlinked = [e for e in all_exp if not (e.get('supplier_id') or '').strip() and not (e.get('supplier_name') or '').strip()]
print(f"Total unlinked: {len(unlinked)}")
cats = {}
for e in unlinked:
    c = e.get('category','unknown')
    cats[c] = cats.get(c, 0) + 1
for c, n in cats.items():
    print(f"  category={c!r}: {n} records")

# Show sample of unlinked
for e in unlinked[:10]:
    print(f"  {e['id'][:15]} | cat={e.get('category','')!r:20} | desc={e.get('description','')!r:30} | mat={e.get('material_type','')!r}")

# ── 5. Verify final supplier count ────────────────────────────────────────
print("\n=== Final supplier list ===")
final_sups = get('suppliers?select=id,company_name,materials_supplied')
print(f"Total: {len(final_sups)}")
for s in final_sups:
    exp_count = get(f"expenses?select=id&supplier_id=eq.{s['id']}&limit=500")
    print(f"  {s['company_name']:20} | {s['id']:20} | expenses: {len(exp_count)}")
