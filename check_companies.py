import os
os.environ['SUPABASE_URL'] = 'https://gdmijolkdpfkacnljdfo.supabase.co'
os.environ['SUPABASE_KEY'] = 'sb_publishable_gS8nPQmJ6qEHxhlKJDo5Aw_J9PVdzGD'
from supabase import create_client
from collections import defaultdict

client = create_client(os.environ['SUPABASE_URL'], os.environ['SUPABASE_KEY'])
resp = client.table('manual_billing').select('*').limit(10000).execute()
print(f'Total records: {len(resp.data)}')

companies = defaultdict(lambda: {'count': 0, 'm3': 0, 'amount': 0, 'advance': 0})
for r in resp.data:
    name = repr(r.get('company_name', ''))
    companies[name]['count'] += 1
    companies[name]['m3'] += float(r.get('cubic_meters', 0) or 0)
    companies[name]['amount'] += float(r.get('total_amount', 0) or 0)
    companies[name]['advance'] += float(r.get('advance_amount', 0) or 0)

print()
for name, vals in sorted(companies.items()):
    c = vals['count']
    m = vals['m3']
    a = vals['amount']
    print(f"{name}: {c} records, m3={m}, amount={a}")
