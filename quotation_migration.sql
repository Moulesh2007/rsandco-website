-- quotation_migration.sql
-- Run this in your Supabase SQL Editor to add the Quotation module

-- 1. Create Tables

-- Quotations table
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

-- Quotation line items
CREATE TABLE IF NOT EXISTS rmc_quotation_items (
    id text PRIMARY KEY,
    quotation_id text NOT NULL,
    description text NOT NULL,
    quantity numeric DEFAULT 0,
    unit text DEFAULT 'cu.m',
    rate numeric DEFAULT 0,
    amount numeric DEFAULT 0
);

-- Quotation settings (configurable T&C)
CREATE TABLE IF NOT EXISTS rmc_quotation_settings (
    id text PRIMARY KEY,
    default_terms text,
    default_validity_days integer DEFAULT 15,
    updated_at text,
    updated_by text
);


-- 2. Enable Row Level Security (RLS)
ALTER TABLE rmc_quotations ENABLE ROW LEVEL SECURITY;
ALTER TABLE rmc_quotation_items ENABLE ROW LEVEL SECURITY;
ALTER TABLE rmc_quotation_settings ENABLE ROW LEVEL SECURITY;


-- 3. Create Policies (Allow full access for authenticated backend)
-- Following the existing pattern for the Python Backend (Anon Role)
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
