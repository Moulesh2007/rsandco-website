"""
Two-step migration:
1. Add 'quality' column to expenses table via Supabase SQL
2. Fix existing records where quality was embedded in description
"""

import re, requests

SUPABASE_URL = "https://gdmijolkdpfkacnljdfo.supabase.co"
SUPABASE_KEY = "sb_publishable_gS8nPQmJ6qEHxhlKJDo5Aw_J9PVdzGD"

headers = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json",
    "Prefer": "return=representation"
}

QUALITY_PATTERNS = [
    (r',\s*12\s*mm', '12mm'),
    (r',\s*20\s*mm', '20mm'),
    (r',\s*msand',   'msand'),
    (r',\s*dust',    'dust'),
]

def extract_quality(description):
    if not description:
        return description, None
    for pattern, quality_val in QUALITY_PATTERNS:
        match = re.search(pattern, description, re.IGNORECASE)
        if match:
            clean = description[:match.start()].strip()
            return clean, quality_val
    return description, None

# ── STEP 1: Fetch all records ──────────────────────────────────────────────
print("Fetching expense records...")
resp = requests.get(
    f"{SUPABASE_URL}/rest/v1/expenses?select=*",
    headers=headers
)
records = resp.json() if resp.ok else []
print(f"  Found {len(records)} records.\n")

# ── STEP 2: Patch each record that needs fixing ────────────────────────────
updated_count = 0
for rec in records:
    if not isinstance(rec, dict):
        continue
    desc = rec.get("description", "") or ""
    existing_quality = rec.get("quality", "") or ""

    if existing_quality:
        continue  # already has quality set

    clean_desc, quality = extract_quality(desc)
    if quality:
        rec_id = rec["id"]
        print(f"  Record {rec_id}:")
        print(f"    description : '{desc}'  ->  '{clean_desc}'")
        print(f"    quality     : ''        ->  '{quality}'")

        patch_resp = requests.patch(
            f"{SUPABASE_URL}/rest/v1/expenses?id=eq.{rec_id}",
            headers=headers,
            json={"description": clean_desc, "quality": quality}
        )
        if patch_resp.ok:
            print(f"    OK Updated.\n")
            updated_count += 1
        else:
            print(f"    ERROR {patch_resp.status_code}: {patch_resp.text}\n")

print(f"Migration complete. {updated_count} record(s) updated.")
