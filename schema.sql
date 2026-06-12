-- schema.sql
-- Run this in your Supabase SQL Editor

-- 1. Create tables

-- Drop tables if they exist
drop table if exists contact_submissions cascade;
drop table if exists newsletter_subscribers cascade;
drop table if exists founder_ceo cascade;
drop table if exists plants cascade;
drop table if exists projects cascade;

-- Founder & CEO Table
create table founder_ceo (
    id uuid primary key default gen_random_uuid(),
    name text not null,
    role text not null,
    bio text not null,
    photo_url text not null,
    vision text not null,
    created_at timestamp with time zone default now()
);

-- Plants Table
create table plants (
    id uuid primary key default gen_random_uuid(),
    name text not null,
    type text not null check (type in ('Hotmix', 'RMC')),
    capacity text not null,
    status text not null check (status in ('Active', 'Maintenance', 'Offline')),
    live_metrics jsonb not null default '{}'::jsonb,
    address text,
    map_url text,
    last_updated timestamp with time zone default now(),
    created_at timestamp with time zone default now()
);

-- Projects Table
create table projects (
    id uuid primary key default gen_random_uuid(),
    name text not null,
    description text not null,
    progress integer not null default 0 check (progress >= 0 and progress <= 100),
    image_url text not null,
    status text not null check (status in ('Ongoing', 'Completed', 'Upcoming')),
    created_at timestamp with time zone default now()
);

-- Contact Submissions Table
create table contact_submissions (
    id uuid primary key default gen_random_uuid(),
    name text not null,
    email text not null,
    message text not null,
    submitted_at timestamp with time zone default now()
);

-- Newsletter Subscribers Table
create table newsletter_subscribers (
    id uuid primary key default gen_random_uuid(),
    email text unique not null,
    subscribed_at timestamp with time zone default now()
);

-- Enable Row Level Security (RLS) for all tables
alter table founder_ceo enable row level security;
alter table plants enable row level security;
alter table projects enable row level security;
alter table contact_submissions enable row level security;
alter table newsletter_subscribers enable row level security;

-- Create Policies (Read is public, Write requires authenticated user)
create policy "Allow public read access to founder_ceo" on founder_ceo for select using (true);
create policy "Allow public read access to plants" on plants for select using (true);
create policy "Allow public read access to projects" on projects for select using (true);

create policy "Allow public insert to contact_submissions" on contact_submissions for insert with check (true);
create policy "Allow public insert to newsletter_subscribers" on newsletter_subscribers for insert with check (true);

-- Admin write policies (For dashboard)
create policy "Allow admin write access to founder_ceo" on founder_ceo for all using (auth.role() = 'authenticated');
create policy "Allow admin write access to plants" on plants for all using (auth.role() = 'authenticated');
create policy "Allow admin write access to projects" on projects for all using (auth.role() = 'authenticated');
create policy "Allow admin read access to contact_submissions" on contact_submissions for select using (auth.role() = 'authenticated');
create policy "Allow admin read access to newsletter_subscribers" on newsletter_subscribers for select using (auth.role() = 'authenticated');


-- 2. Insert Seed Data

-- Seed Founder & CEO
insert into founder_ceo (name, role, bio, photo_url, vision)
values (
    'S Maghesh',
    'Founder & Chief Executive Officer',
    'With over 25 years of pioneering leadership in infrastructure development, S Maghesh has steered RS & CO from a local paving contractor to an elite infrastructure enterprise. His engineering acumen paired with an uncompromising commitment to premium execution has redefined highway construction standards across the region.',
    'https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?auto=format&fit=crop&q=80&w=600',
    'To build foundational pathways that endure for generations, fusing cutting-edge materials engineering with timeless architectural luxury and safety.'
);

-- Seed Plants
insert into plants (name, type, capacity, status, live_metrics, address, map_url)
values 
(
    'Golden Falcon Hotmix Plant',
    'Hotmix',
    '160 TPH',
    'Active',
    '{"temperature": "165°C", "hourly_output": "142 tons", "fuel_efficiency": "94%", "active_recipe": "Superpave PG 76-22"}'::jsonb,
    null,
    null
),
(
    'R. Sundaram & Co. RMC Plant',
    'RMC',
    '90 m³/hr',
    'Active',
    '{"active_mix": "M25 (High Durability)", "current_slump": "120mm", "silo_levels": {"cement": "84%", "flyash": "72%"}, "water_cement_ratio": "0.42"}'::jsonb,
    'Quarry Rd, Tiruneermalai, Chennai, Tamil Nadu 600132',
    'https://maps.app.goo.gl/E94H9iCz8hXbowjo9'
),
(
    'Imperial Hotmix Plant 2',
    'Hotmix',
    '120 TPH',
    'Maintenance',
    '{"temperature": "45°C", "hourly_output": "0 tons", "maintenance_reason": "Scheduled burner nozzle calibration", "estimated_resume": "2 hours"}'::jsonb,
    null,
    null
);

-- Seed Projects
insert into projects (name, description, progress, image_url, status)
values
(
    'The Grand Horizon Expressway',
    'An elite 8-lane concrete highway connecting major industrial corridors, integrating automated tollways and sustainable green zones.',
    85,
    'https://images.unsplash.com/photo-1541888946425-d81bb19240f5?auto=format&fit=crop&q=80&w=800',
    'Ongoing'
),
(
    'Royal Vista Bridge & Flyover',
    'A majestic pre-stressed concrete flyover utilizing premium grade M45 concrete and architectural LED lighting accents.',
    100,
    'https://images.unsplash.com/photo-1513828729170-d62b358730eb?auto=format&fit=crop&q=80&w=800',
    'Completed'
),
(
    'Aurelia Boulevard Corridor',
    'Urban revitalization paving project featuring advanced noise-reducing stone mastic asphalt and luxury pedestrian pathways.',
    30,
    'https://images.unsplash.com/photo-1504307651254-35680f356dfd?auto=format&fit=crop&q=80&w=800',
    'Ongoing'
);

-- ==================== RMC MODULE TABLES ====================

-- Drop RMC tables if they exist
drop table if exists rmc_payment_records cascade;
drop table if exists rmc_invoices cascade;
drop table if exists rmc_order_items cascade;
drop table if exists rmc_orders cascade;
drop table if exists rmc_clients cascade;
drop table if exists rmc_concrete_grades cascade;
drop table if exists rmc_users cascade;

-- Users Table for Authentication
create table rmc_users (
    id uuid primary key default gen_random_uuid(),
    username text not null unique,
    email text not null unique,
    password_hash text not null,
    full_name text not null,
    role text not null check (role in ('client', 'admin', 'manager')),
    phone text,
    is_active boolean default true,
    created_at timestamp with time zone default now(),
    updated_at timestamp with time zone default now()
);

-- Enable RLS on users table
alter table rmc_users enable row level security;

-- RLS Policies for users table
create policy "Users can view their own profile" on rmc_users for select using (id = auth.uid());
create policy "Users can update their own profile" on rmc_users for update using (id = auth.uid());
create policy "Admins can view all users" on rmc_users for select using (
    exists (select 1 from rmc_users where id = auth.uid() and role = 'admin')
);
create policy "Admins can insert users" on rmc_users for insert with check (
    exists (select 1 from rmc_users where id = auth.uid() and role = 'admin')
);
create policy "Admins can update users" on rmc_users for update using (
    exists (select 1 from rmc_users where id = auth.uid() and role = 'admin')
);

-- Concrete Grades Table
create table rmc_concrete_grades (
    id uuid primary key default gen_random_uuid(),
    grade_code text not null unique,
    grade_name text not null,
    description text,
    price_per_cubic_meter numeric(10,2) not null,
    is_active boolean default true,
    created_at timestamp with time zone default now()
);

-- Clients Table
create table rmc_clients (
    id uuid primary key default gen_random_uuid(),
    company_name text not null,
    contact_person text not null,
    email text not null,
    phone text not null,
    billing_address text not null,
    shipping_address text,
    gst_number text,
    credit_limit numeric(12,2) default 0,
    current_balance numeric(12,2) default 0,
    is_active boolean default true,
    created_at timestamp with time zone default now(),
    updated_at timestamp with time zone default now()
);

-- Orders Table
create table rmc_orders (
    id uuid primary key default gen_random_uuid(),
    order_number text not null unique,
    user_id uuid references rmc_users(id),
    client_id uuid references rmc_clients(id),
    customer_name text,
    phone text,
    order_date timestamp with time zone default now(),
    delivery_date date,
    delivery_address text,
    status text not null check (status in ('Pending', 'Approved', 'In Production', 'Dispatched', 'Delivered', 'Cancelled', 'On Hold')),
    total_amount numeric(12,2) not null default 0,
    notes text,
    created_by text,
    approved_by text,
    approved_at timestamp with time zone,
    created_at timestamp with time zone default now(),
    updated_at timestamp with time zone default now()
);

-- Order Items Table
create table rmc_order_items (
    id uuid primary key default gen_random_uuid(),
    order_id uuid not null references rmc_orders(id) on delete cascade,
    grade_id uuid not null references rmc_concrete_grades(id),
    quantity_cubic_meters numeric(10,2) not null,
    unit_price numeric(10,2) not null,
    subtotal numeric(12,2) not null,
    created_at timestamp with time zone default now()
);

-- Invoices Table
create table rmc_invoices (
    id uuid primary key default gen_random_uuid(),
    invoice_number text not null unique,
    order_id uuid not null references rmc_orders(id),
    client_id uuid not null references rmc_clients(id),
    invoice_date date not null default current_date,
    due_date date not null,
    subtotal numeric(12,2) not null,
    tax_amount numeric(12,2) not null default 0,
    total_amount numeric(12,2) not null,
    status text not null check (status in ('Draft', 'Sent', 'Paid', 'Overdue', 'Cancelled')),
    payment_terms text,
    notes text,
    created_at timestamp with time zone default now(),
    updated_at timestamp with time zone default now()
);

-- Payment Records Table
create table rmc_payment_records (
    id uuid primary key default gen_random_uuid(),
    payment_number text not null unique,
    invoice_id uuid references rmc_invoices(id),
    client_id uuid not null references rmc_clients(id),
    payment_date date not null default current_date,
    amount numeric(12,2) not null,
    payment_method text not null check (payment_method in ('Bank Transfer', 'Cheque', 'Cash', 'UPI', 'Online')),
    reference_number text,
    notes text,
    created_at timestamp with time zone default now()
);

-- Enable RLS for RMC tables
alter table rmc_concrete_grades enable row level security;
alter table rmc_clients enable row level security;
alter table rmc_orders enable row level security;
alter table rmc_order_items enable row level security;
alter table rmc_invoices enable row level security;
alter table rmc_payment_records enable row level security;

-- Public read policies for clients (their own data)
create policy "Clients can read own data" on rmc_clients for select using (true);
create policy "Public can read concrete grades" on rmc_concrete_grades for select using (true);

-- Admin policies
create policy "Admin full access to concrete grades" on rmc_concrete_grades for all using (auth.role() = 'authenticated');
create policy "Admin full access to clients" on rmc_clients for all using (auth.role() = 'authenticated');
create policy "Admin full access to orders" on rmc_orders for all using (auth.role() = 'authenticated');
create policy "Admin full access to order items" on rmc_order_items for all using (auth.role() = 'authenticated');
create policy "Admin full access to invoices" on rmc_invoices for all using (auth.role() = 'authenticated');
create policy "Admin full access to payments" on rmc_payment_records for all using (auth.role() = 'authenticated');

-- Public insert for client orders (via API)
create policy "Public can insert orders" on rmc_orders for insert with check (true);
create policy "Public can insert order items" on rmc_order_items for insert with check (true);

-- Seed Concrete Grades
insert into rmc_concrete_grades (grade_code, grade_name, description, price_per_cubic_meter)
values
('M10', 'M10 Grade', 'Standard concrete for non-structural applications', 4500.00),
('M15', 'M15 Grade', 'Light duty concrete for pathways and floors', 4800.00),
('M20', 'M20 Grade', 'Standard grade for residential construction', 5200.00),
('M25', 'M25 Grade', 'High durability concrete for commercial buildings', 5600.00),
('M30', 'M30 Grade', 'Premium grade for heavy structural applications', 6100.00),
('M35', 'M35 Grade', 'Ultra-high strength for specialized infrastructure', 6800.00),
('M40', 'M40 Grade', 'Elite grade for critical infrastructure projects', 7500.00);

-- Seed Sample Client
insert into rmc_clients (company_name, contact_person, email, phone, billing_address, gst_number, credit_limit)
values
('Apex Construction Ltd', 'Rajesh Kumar', 'rajesh@apexconstruction.com', '+91 98765 43210', '123 Industrial Area, Chennai, Tamil Nadu 600001', '33AABCU9603R1ZN', 5000000.00);

-- Seed Users (passwords should be hashed in production, using plain text for mock data)
insert into rmc_users (username, email, password_hash, full_name, role, phone)
values
('admin', 'admin@rsandco.com', 'admin123', 'System Administrator', 'admin', '+91 98765 43211'),
('manager', 'manager@rsandco.com', 'manager123', 'Operations Manager', 'manager', '+91 98765 43212');
