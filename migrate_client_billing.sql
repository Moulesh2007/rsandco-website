-- Run this in Supabase SQL Editor for existing databases
-- Adds Client Billing Summary support without dropping data

alter table manual_billing add column if not exists billing_status text default 'unbilled';
alter table manual_billing add column if not exists billing_summary_id text;

update manual_billing
set billing_status = 'unbilled'
where billing_status is null;

create table if not exists client_billing_summaries (
    id text primary key,
    invoice_number text unique not null,
    client_name text not null,
    bill_date text not null,
    total_amount numeric default 0,
    advance_deducted numeric default 0,
    balance_amount numeric default 0,
    advance_carried_forward numeric default 0,
    transaction_ids text,
    pdf_path text,
    pdf_filename text,
    notes text,
    created_at text,
    created_by text
);

alter table client_billing_summaries enable row level security;

drop policy if exists "Allow full access to client_billing_summaries" on client_billing_summaries;
create policy "Allow full access to client_billing_summaries" on client_billing_summaries for all using (true);
