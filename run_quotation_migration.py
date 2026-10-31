"""
run_quotation_migration.py
--------------------------
Runs the quotation migration against Supabase using the service-role key.

Usage:
    python run_quotation_migration.py --service-role-key YOUR_SERVICE_ROLE_KEY

Or set SUPABASE_SERVICE_ROLE_KEY in your .env file and just run:
    python run_quotation_migration.py
"""

import os
import sys
import argparse
import requests
from dotenv import load_dotenv

load_dotenv()

MIGRATION_SQL = """
CREATE TABLE IF NOT EXISTS rmc_quotations (
    id text PRIMARY KEY,
    quotation_number text UNIQUE NOT NULL,
    client_id text,
    client_name text,
    company_name text,
    address text,
    phone text,
    email text,
    client_gst_number text,
    quotation_date text,
    validity_days integer DEFAULT 15,
    validity_date text,
    include_gst boolean DEFAULT false,
    gst_type text DEFAULT 'intra',
    subtotal numeric DEFAULT 0,
    cgst_amount numeric DEFAULT 0,
    sgst_amount numeric DEFAULT 0,
    igst_amount numeric DEFAULT 0,
    grand_total numeric DEFAULT 0,
    terms_and_conditions text,
    status text DEFAULT 'Draft',
    notes text,
    created_at text,
    created_by text
)
"""

MIGRATION_ITEMS_SQL = """
CREATE TABLE IF NOT EXISTS rmc_quotation_items (
    id text PRIMARY KEY,
    quotation_id text NOT NULL,
    description text NOT NULL,
    quantity numeric DEFAULT 0,
    unit text DEFAULT 'cu.m',
    rate numeric DEFAULT 0,
    amount numeric DEFAULT 0
)
"""

MIGRATION_SETTINGS_SQL = """
CREATE TABLE IF NOT EXISTS rmc_quotation_settings (
    id text PRIMARY KEY,
    default_terms text,
    default_validity_days integer DEFAULT 15,
    updated_at text,
    updated_by text
)
"""

RLS_QUOTATIONS = "ALTER TABLE rmc_quotations ENABLE ROW LEVEL SECURITY"
RLS_ITEMS = "ALTER TABLE rmc_quotation_items ENABLE ROW LEVEL SECURITY"
RLS_SETTINGS = "ALTER TABLE rmc_quotation_settings ENABLE ROW LEVEL SECURITY"

POLICY_QUOTATIONS = 'CREATE POLICY "Allow all to quotations" ON rmc_quotations FOR ALL USING (true)'
POLICY_ITEMS = 'CREATE POLICY "Allow all to quotation_items" ON rmc_quotation_items FOR ALL USING (true)'
POLICY_SETTINGS = 'CREATE POLICY "Allow all to quotation_settings" ON rmc_quotation_settings FOR ALL USING (true)'

SEED_SETTINGS = """
INSERT INTO rmc_quotation_settings (id, default_terms, default_validity_days, updated_at)
VALUES (
    'default',
    '["Prices are subject to change without prior notice.", "Payment terms: 50% advance, balance on delivery / as agreed.", "Delivery subject to plant availability and site accessibility.", "Rates valid only for the validity period mentioned above.", "Any additional cartage/pumping charges extra as applicable.", "Taxes as applicable at the time of billing.", "Disputes subject to Chennai jurisdiction only."]',
    15,
    '2026-09-12T00:00:00.000Z'
) ON CONFLICT (id) DO NOTHING
"""

ALL_STATEMENTS = [
    ("Create rmc_quotations table", MIGRATION_SQL),
    ("Create rmc_quotation_items table", MIGRATION_ITEMS_SQL),
    ("Create rmc_quotation_settings table", MIGRATION_SETTINGS_SQL),
    ("Enable RLS on rmc_quotations", RLS_QUOTATIONS),
    ("Enable RLS on rmc_quotation_items", RLS_ITEMS),
    ("Enable RLS on rmc_quotation_settings", RLS_SETTINGS),
    ("Create policy for rmc_quotations", POLICY_QUOTATIONS),
    ("Create policy for rmc_quotation_items", POLICY_ITEMS),
    ("Create policy for rmc_quotation_settings", POLICY_SETTINGS),
    ("Seed default quotation settings", SEED_SETTINGS),
]

FULL_SQL_FOR_EDITOR = """-- quotation_migration.sql
-- Run this in your Supabase SQL Editor

-- 1. Create Tables
CREATE TABLE IF NOT EXISTS rmc_quotations (
    id text PRIMARY KEY,
    quotation_number text UNIQUE NOT NULL,
    client_id text,
    client_name text,
    company_name text,
    address text,
    phone text,
    email text,
    client_gst_number text,
    quotation_date text,
    validity_days integer DEFAULT 15,
    validity_date text,
    include_gst boolean DEFAULT false,
    gst_type text DEFAULT 'intra',
    subtotal numeric DEFAULT 0,
    cgst_amount numeric DEFAULT 0,
    sgst_amount numeric DEFAULT 0,
    igst_amount numeric DEFAULT 0,
    grand_total numeric DEFAULT 0,
    terms_and_conditions text,
    status text DEFAULT 'Draft',
    notes text,
    created_at text,
    created_by text
);

CREATE TABLE IF NOT EXISTS rmc_quotation_items (
    id text PRIMARY KEY,
    quotation_id text NOT NULL,
    description text NOT NULL,
    quantity numeric DEFAULT 0,
    unit text DEFAULT 'cu.m',
    rate numeric DEFAULT 0,
    amount numeric DEFAULT 0
);

CREATE TABLE IF NOT EXISTS rmc_quotation_settings (
    id text PRIMARY KEY,
    default_terms text,
    default_validity_days integer DEFAULT 15,
    updated_at text,
    updated_by text
);

-- 2. Enable Row Level Security
ALTER TABLE rmc_quotations ENABLE ROW LEVEL SECURITY;
ALTER TABLE rmc_quotation_items ENABLE ROW LEVEL SECURITY;
ALTER TABLE rmc_quotation_settings ENABLE ROW LEVEL SECURITY;

-- 3. Create Policies
CREATE POLICY "Allow all to quotations" ON rmc_quotations FOR ALL USING (true);
CREATE POLICY "Allow all to quotation_items" ON rmc_quotation_items FOR ALL USING (true);
CREATE POLICY "Allow all to quotation_settings" ON rmc_quotation_settings FOR ALL USING (true);

-- 4. Seed Default Settings
INSERT INTO rmc_quotation_settings (id, default_terms, default_validity_days, updated_at)
VALUES (
    'default',
    '["Prices are subject to change without prior notice.", "Payment terms: 50% advance, balance on delivery / as agreed.", "Delivery subject to plant availability and site accessibility.", "Rates valid only for the validity period mentioned above.", "Any additional cartage/pumping charges extra as applicable.", "Taxes as applicable at the time of billing.", "Disputes subject to Chennai jurisdiction only."]',
    15,
    '2026-09-12T00:00:00.000Z'
) ON CONFLICT (id) DO NOTHING;
"""


def run_migration(supabase_url, service_role_key):
    project_ref = supabase_url.replace("https://", "").replace(".supabase.co", "")
    headers = {
        "Authorization": "Bearer " + service_role_key,
        "Content-Type": "application/json",
    }
    api_url = "https://api.supabase.com/v1/projects/" + project_ref + "/database/query"

    print("\nConnecting to Supabase project: " + project_ref)
    print("-" * 55)

    success_count = 0
    error_count = 0

    for label, stmt in ALL_STATEMENTS:
        resp = requests.post(api_url, headers=headers, json={"query": stmt.strip() + ";"})
        if resp.status_code in (200, 201):
            print("  [OK]   " + label)
            success_count += 1
        else:
            err = resp.json() if resp.headers.get("content-type", "").startswith("application/json") else resp.text
            # Ignore "already exists" errors for policies/tables
            err_str = str(err)
            if "already exists" in err_str or "duplicate" in err_str.lower():
                print("  [SKIP] " + label + " (already exists)")
                success_count += 1
            else:
                print("  [FAIL] " + label + " -- " + str(resp.status_code) + ": " + err_str[:150])
                error_count += 1

    print("\n" + "-" * 55)
    print("Succeeded: " + str(success_count) + "  |  Failed: " + str(error_count))

    if error_count == 0:
        print("\nMigration completed successfully!")
        print("Quotation tables are now ready in Supabase.")
    else:
        print("\nSome statements failed. Try running the SQL manually in the Supabase SQL Editor.")
        print_manual_instructions(project_ref)


def verify_tables(supabase_url, key):
    from supabase import create_client
    client = create_client(supabase_url, key)
    tables = ["rmc_quotations", "rmc_quotation_items", "rmc_quotation_settings"]
    print("\nVerifying tables...")
    all_ok = True
    for table in tables:
        try:
            r = client.table(table).select("id").limit(1).execute()
            print("  [OK]   " + table + ": accessible")
        except Exception as e:
            print("  [FAIL] " + table + ": NOT accessible -- " + str(e)[:100])
            all_ok = False
    if all_ok:
        print("\nAll quotation tables are accessible. Quotation data will now be stored in Supabase!")
    else:
        print("\nSome tables are still missing. Please run the SQL in Supabase SQL Editor.")
    return all_ok


def print_manual_instructions(project_ref):
    print("\n" + "=" * 55)
    print("MANUAL STEPS:")
    print("1. Go to: https://supabase.com/dashboard/project/" + project_ref + "/sql/new")
    print("2. Paste the SQL from quotation_migration.sql")
    print("3. Click 'Run'")
    print("=" * 55)
    print("\nSQL Content (from quotation_migration.sql):")
    print(FULL_SQL_FOR_EDITOR)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run quotation migration against Supabase.")
    parser.add_argument("--service-role-key", help="Supabase service role key", default=None)
    parser.add_argument("--verify-only", action="store_true", help="Only verify tables exist, do not run migration")
    args = parser.parse_args()

    supabase_url = os.getenv("SUPABASE_URL")
    if not supabase_url:
        print("[ERROR] SUPABASE_URL not found in environment. Set it in .env")
        sys.exit(1)

    anon_key = os.getenv("SUPABASE_KEY") or os.getenv("SUPABASE_ANON_KEY")

    if args.verify_only:
        if not anon_key:
            print("[ERROR] SUPABASE_KEY not found in environment.")
            sys.exit(1)
        ok = verify_tables(supabase_url, anon_key)
        sys.exit(0 if ok else 1)

    service_role_key = (
        args.service_role_key
        or os.getenv("SUPABASE_SERVICE_ROLE_KEY")
        or os.getenv("SUPABASE_SERVICE_ROLE")
        or os.getenv("SUPABASE_SERVICE_KEY")
    )

    if not service_role_key:
        print("\n[ERROR] No service role key provided.")
        print("\nTo run the migration automatically, you need your Supabase SERVICE ROLE key.")
        print("Find it at: Supabase Dashboard -> Your Project -> Settings -> API -> service_role key")
        print("\nOption 1 - Add to .env:")
        print("  SUPABASE_SERVICE_ROLE_KEY=your_service_role_key_here")
        print("  python run_quotation_migration.py")
        print("\nOption 2 - Pass as argument:")
        print("  python run_quotation_migration.py --service-role-key YOUR_KEY")
        project_ref = supabase_url.replace("https://", "").replace(".supabase.co", "")
        print_manual_instructions(project_ref)
        sys.exit(1)

    run_migration(supabase_url, service_role_key)

    if anon_key:
        verify_tables(supabase_url, anon_key)
