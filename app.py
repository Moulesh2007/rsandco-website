# app.py
import os
import logging
import uuid
import secrets
from datetime import datetime, date, timedelta
from flask import Flask, jsonify, request, render_template, send_from_directory, make_response, session, redirect, url_for
from dotenv import load_dotenv
from supabase import create_client, Client
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from werkzeug.security import generate_password_hash, check_password_hash

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

app = Flask(__name__, template_folder='templates', static_folder='static')
app.config['SECRET_KEY'] = os.getenv('FLASK_SECRET_KEY', 'rs-co-default-luxury-secret-key')
app.config['SESSION_COOKIE_SECURE'] = True
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'

# CSRF Protection
def generate_csrf_token():
    if 'csrf_token' not in session:
        session['csrf_token'] = secrets.token_hex(32)
    return session['csrf_token']

def validate_csrf_token(token):
    return 'csrf_token' in session and secrets.compare_digest(session['csrf_token'], token)

app.jinja_env.globals['csrf_token'] = lambda: generate_csrf_token()

# Simple Rate Limiter
rate_limit_storage = {}

def check_rate_limit(identifier, max_requests=5, window_seconds=60):
    current_time = datetime.now()
    if identifier not in rate_limit_storage:
        rate_limit_storage[identifier] = []
    
    # Remove old requests outside the time window
    rate_limit_storage[identifier] = [
        req_time for req_time in rate_limit_storage[identifier]
        if (current_time - req_time).total_seconds() < window_seconds
    ]
    
    # Check if limit exceeded
    if len(rate_limit_storage[identifier]) >= max_requests:
        return False
    
    # Add current request
    rate_limit_storage[identifier].append(current_time)
    return True

# Supabase Initialization with Fallback
SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_KEY')
SUPABASE_CLIENT = None

# ─── FILE-BASED PERSISTENCE ─────────────────────────────────────────────────
import json

DB_FILE = os.path.join(os.path.dirname(__file__), 'data', 'db.json')

# Keys that are user-created and must be persisted across restarts
PERSISTED_KEYS = ['manual_billing', 'expenses', 'rmc_orders', 'rmc_order_items',
                   'rmc_invoices', 'rmc_payments', 'rmc_clients', 'submissions', 'newsletter',
                   'rmc_users']

def save_db():
    """Persist dynamic user data to disk."""
    try:
        os.makedirs(os.path.dirname(DB_FILE), exist_ok=True)
        payload = {k: MOCK_DATABASE.get(k, []) for k in PERSISTED_KEYS}
        with open(DB_FILE, 'w', encoding='utf-8') as f:
            json.dump(payload, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logger.error(f"save_db error: {e}")

def load_db():
    """Load persisted user data from disk into MOCK_DATABASE."""
    if not os.path.exists(DB_FILE):
        return
    try:
        with open(DB_FILE, 'r', encoding='utf-8') as f:
            payload = json.load(f)
        for k in PERSISTED_KEYS:
            if k in payload:
                MOCK_DATABASE[k] = payload[k]
        logger.info(f"Loaded persisted data: {', '.join(f'{k}={len(MOCK_DATABASE.get(k,[]))}' for k in PERSISTED_KEYS if isinstance(MOCK_DATABASE.get(k), list))}")
    except Exception as e:
        logger.error(f"load_db error: {e}")

# ─────────────────────────────────────────────────────────────────────────────
# Mock In-Memory Database for local preview/fallback
MOCK_DATABASE = {
    "founder": {
        "name": "S Maghesh",
        "role": "Founder & Chief Executive Officer",
        "bio": "With over 25 years of pioneering leadership in infrastructure development, S Maghesh has steered RS & CO from a local paving contractor to an elite infrastructure enterprise. His engineering acumen paired with an uncompromising commitment to premium execution has redefined highway construction standards across the region.",
        "photo_url": "/static/images/founder_ceo.jpg",
        "vision": "To build foundational pathways that endure for generations, fusing cutting-edge materials engineering with timeless architectural luxury and safety."
    },
    "rmc_users": [
        {
            "id": "user-1",
            "username": "admin",
            "email": "admin@rsandco.com",
            "password_hash": generate_password_hash("admin123"),
            "full_name": "System Administrator",
            "role": "admin",
            "phone": "+91 98765 43211",
            "is_active": True
        },
        {
            "id": "user-2",
            "username": "manager",
            "email": "manager@rsandco.com",
            "password_hash": generate_password_hash("manager123"),
            "full_name": "Operations Manager",
            "role": "manager",
            "phone": "+91 98765 43212",
            "is_active": True
        },
        {
            "id": "user-3",
            "username": "client",
            "email": "client@test.com",
            "password_hash": generate_password_hash("client123"),
            "full_name": "Test Client",
            "role": "client",
            "phone": "+91 98765 43213",
            "is_active": True
        }
    ],
    "manual_billing": [
        {
            "id": "bill-1",
            "company_name": "ABC Construction Ltd",
            "phone": "9876543210",
            "address": "123 Main St, Chennai",
            "date": "2025-12-11",
            "time": "10:30 AM",
            "vehicle_number": "TN-01-AB-1234",
            "driver_name": "R Kumar",
            "grade": "M25",
            "cubic_meters": 5.5,
            "rate_per_cubic": 4500,
            "total_amount": 24750,
            "advance_amount": 10000,
            "balance_amount": 14750,
            "loading_time": "09:45 AM",
            "unloading_time": "10:30 AM",
            "created_at": "2025-12-11T10:30:00"
        },
        {
            "id": "bill-2",
            "company_name": "XYZ Builders",
            "phone": "9876543211",
            "address": "456 Oak Ave, Chennai",
            "date": "2025-12-10",
            "time": "02:15 PM",
            "vehicle_number": "TN-02-CD-5678",
            "driver_name": "S Raj",
            "grade": "M30",
            "cubic_meters": 8.0,
            "rate_per_cubic": 4800,
            "total_amount": 38400,
            "advance_amount": 15000,
            "balance_amount": 23400,
            "loading_time": "01:30 PM",
            "unloading_time": "02:15 PM",
            "created_at": "2025-12-10T14:15:00"
        }
    ],
    "expenses": [],
    "plants": [
        {
            "id": "plant-1",
            "name": "Golden Falcon Hotmix Plant",
            "type": "Hotmix",
            "capacity": "160 TPH",
            "status": "Active",
            "live_metrics": {
                "temperature": "165°C",
                "hourly_output": "142 tons",
                "fuel_efficiency": "94%",
                "active_recipe": "Superpave PG 76-22"
            },
            "last_updated": "Just now"
        },
        {
            "id": "plant-2",
            "name": "R. Sundaram & Co. RMC Plant",
            "type": "RMC",
            "capacity": "90 m³/hr",
            "status": "Active",
            "live_metrics": {
                "active_mix": "M25 (High Durability)",
                "current_slump": "120mm",
                "silo_levels": {"cement": "84%", "flyash": "72%"},
                "water_cement_ratio": "0.42"
            },
            "address": "Quarry Rd, Tiruneermalai, Chennai, Tamil Nadu 600132",
            "map_url": "https://maps.app.goo.gl/E94H9iCz8hXbowjo9",
            "last_updated": "Just now"
        },
        {
            "id": "plant-3",
            "name": "Imperial Hotmix Plant 2",
            "type": "Hotmix",
            "capacity": "120 TPH",
            "status": "Maintenance",
            "live_metrics": {
                "temperature": "45°C",
                "hourly_output": "0 tons",
                "maintenance_reason": "Scheduled burner nozzle calibration",
                "estimated_resume": "2 hours"
            },
            "last_updated": "Just now"
        }
    ],
    "projects": [
        {
            "id": "project-1",
            "name": "The Grand Horizon Expressway",
            "description": "An elite 8-lane concrete highway connecting major industrial corridors, integrating automated tollways and sustainable green zones.",
            "progress": 85,
            "image_url": "https://images.unsplash.com/photo-1541888946425-d81bb19240f5?auto=format&fit=crop&q=80&w=800",
            "status": "Ongoing"
        },
        {
            "id": "project-2",
            "name": "Royal Vista Bridge & Flyover",
            "description": "A majestic pre-stressed concrete flyover utilizing premium grade M45 concrete and architectural LED lighting accents.",
            "progress": 100,
            "image_url": "https://images.unsplash.com/photo-1513828729170-d62b358730eb?auto=format&fit=crop&q=80&w=800",
            "status": "Completed"
        },
        {
            "id": "project-3",
            "name": "Aurelia Boulevard Corridor",
            "description": "Urban revitalization paving project featuring advanced noise-reducing stone mastic asphalt and luxury pedestrian pathways.",
            "progress": 30,
            "image_url": "https://images.unsplash.com/photo-1504307651254-35680f356dfd?auto=format&fit=crop&q=80&w=800",
            "status": "Ongoing"
        }
    ],
    "submissions": [],
    "newsletter": [],
    # RMC Module Mock Data
    "rmc_concrete_grades": [
        {"id": "grade-1", "grade_code": "M10", "grade_name": "M10 Grade", "description": "Standard concrete for non-structural applications", "price_per_cubic_meter": 4500.00, "is_active": True},
        {"id": "grade-2", "grade_code": "M15", "grade_name": "M15 Grade", "description": "Light duty concrete for pathways and floors", "price_per_cubic_meter": 4800.00, "is_active": True},
        {"id": "grade-3", "grade_code": "M20", "grade_name": "M20 Grade", "description": "Standard grade for residential construction", "price_per_cubic_meter": 5200.00, "is_active": True},
        {"id": "grade-4", "grade_code": "M25", "grade_name": "M25 Grade", "description": "High durability concrete for commercial buildings", "price_per_cubic_meter": 5600.00, "is_active": True},
        {"id": "grade-5", "grade_code": "M30", "grade_name": "M30 Grade", "description": "Premium grade for heavy structural applications", "price_per_cubic_meter": 6100.00, "is_active": True},
        {"id": "grade-6", "grade_code": "M35", "grade_name": "M35 Grade", "description": "Ultra-high strength for specialized infrastructure", "price_per_cubic_meter": 6800.00, "is_active": True},
        {"id": "grade-7", "grade_code": "M40", "grade_name": "M40 Grade", "description": "Elite grade for critical infrastructure projects", "price_per_cubic_meter": 7500.00, "is_active": True}
    ],
    "rmc_clients": [
        {
            "id": "client-1",
            "company_name": "Apex Construction Ltd",
            "contact_person": "Rajesh Kumar",
            "email": "rajesh@apexconstruction.com",
            "phone": "+91 98765 43210",
            "billing_address": "123 Industrial Area, Chennai, Tamil Nadu 600001",
            "shipping_address": "123 Industrial Area, Chennai, Tamil Nadu 600001",
            "gst_number": "33AABCU9603R1ZN",
            "credit_limit": 5000000.00,
            "current_balance": 0.00,
            "is_active": True
        }
    ],
    "rmc_orders": [
        {
            "id": "order-1",
            "order_number": "RMC-20260610-0001",
            "user_id": "user-3",
            "customer_name": "Test Customer",
            "phone": "+91 98765 43213",
            "order_date": "2026-06-10T10:00:00",
            "delivery_date": "2026-06-15",
            "delivery_address": "123 Test Street, Chennai",
            "status": "Approved",
            "total_amount": 15000.00,
            "notes": "Test order",
            "items": [
                {
                    "grade_id": "grade-1",
                    "quantity": 5,
                    "unit_price": 3000.00,
                    "subtotal": 15000.00
                }
            ],
            "approved_by": "admin",
            "approved_at": "2026-06-10T10:30:00"
        }
    ],
    "rmc_order_items": [
        {
            "id": "item-1",
            "order_id": "order-1",
            "grade_id": "grade-1",
            "quantity_cubic_meters": 5,
            "unit_price": 3000.00,
            "subtotal": 15000.00
        }
    ],
    "rmc_invoices": [
        {
            "id": "invoice-1",
            "invoice_number": "INV-20260610-0001",
            "order_id": "order-1",
            "invoice_date": "2026-06-10",
            "due_date": "2026-07-10",
            "subtotal": 15000.00,
            "tax_amount": 0,
            "total_amount": 15000.00,
            "status": "Pending",
            "notes": "Auto-generated invoice for order RMC-20260610-0001"
        }
    ],
    "rmc_payments": []
}

if SUPABASE_URL and SUPABASE_KEY:
    try:
        SUPABASE_CLIENT = create_client(SUPABASE_URL, SUPABASE_KEY)
        logger.info("Successfully connected to Supabase.")
    except Exception as e:
        logger.error(f"Error initializing Supabase client: {e}. Falling back to mock database.")
else:
    logger.warning("Supabase credentials not found. App running in LOCAL MOCK DATABASE mode.")
    load_db()  # Restore persisted data on startup

# ----------------- Frontend Routes -----------------
@app.route('/')
def home():
    return render_template('index.html')

@app.route('/admin')
def admin():
    return render_template('admin.html')

@app.route('/login')
def login():
    return render_template('login.html')

@app.route('/register')
def register():
    return render_template('register.html')

@app.route('/robots.txt')
def robots_txt():
    return send_from_directory('static', 'robots.txt')

@app.route('/sitemap.xml')
def sitemap_xml():
    sitemap = '''<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
    <url>
        <loc>https://rsandco.com/</loc>
        <lastmod>2026-06-10</lastmod>
        <changefreq>weekly</changefreq>
        <priority>1.0</priority>
    </url>
    <url>
        <loc>https://rsandco.com/#about</loc>
        <lastmod>2026-06-10</lastmod>
        <changefreq>monthly</changefreq>
        <priority>0.8</priority>
    </url>
    <url>
        <loc>https://rsandco.com/#plants-section</loc>
        <lastmod>2026-06-10</lastmod>
        <changefreq>weekly</changefreq>
        <priority>0.8</priority>
    </url>
    <url>
        <loc>https://rsandco.com/#projects</loc>
        <lastmod>2026-06-10</lastmod>
        <changefreq>weekly</changefreq>
        <priority>0.8</priority>
    </url>
    <url>
        <loc>https://rsandco.com/#contact</loc>
        <lastmod>2026-06-10</lastmod>
        <changefreq>monthly</changefreq>
        <priority>0.6</priority>
    </url>
</urlset>'''
    response = make_response(sitemap)
    response.headers['Content-Type'] = 'application/xml'
    return response

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/billing-expense')
def billing_expense():
    # Role-based access control - only admin and manager can access
    if 'username' not in session:
        return redirect(url_for('login'))
    
    # Check user role from mock database
    user_role = None
    for user in MOCK_DATABASE.get('rmc_users', []):
        if user['username'] == session.get('username'):
            user_role = user['role']
            break
    
    if user_role not in ['admin', 'manager']:
        return jsonify({"error": "Access denied. Admin or Manager role required."}), 403
    
    return render_template('billing_expense.html')

@app.route('/invoice-letterpad')
def invoice_letterpad():
    return render_template('invoice_letterpad.html')

# ----------------- Authentication Routes -----------------
@app.route('/api/auth/login', methods=['POST'])
def api_login():
    # Rate limiting based on IP address
    client_ip = request.remote_addr
    if not check_rate_limit(f"login_{client_ip}", max_requests=5, window_seconds=60):
        return jsonify({"error": "Too many login attempts. Please try again later."}), 429
    
    data = request.json
    username_or_email = data.get('username') or data.get('email')
    password = data.get('password')
    
    if not username_or_email or not password:
        return jsonify({"error": "Missing username/email or password"}), 400
    
    if SUPABASE_CLIENT:
        try:
            # Query user from Supabase
            response = SUPABASE_CLIENT.table("rmc_users").select("*").or_(f"username.eq.{username_or_email},email.eq.{username_or_email}").execute()
            
            if not response.data:
                return jsonify({"error": "Invalid credentials"}), 401
            
            user = response.data[0]
            
            if not user['is_active']:
                return jsonify({"error": "Account is inactive"}), 401
            
            if not check_password_hash(user['password_hash'], password):
                return jsonify({"error": "Invalid credentials"}), 401
            
            # Set session
            session['user_id'] = str(user['id'])
            session['username'] = user['username']
            session['role'] = user['role']
            session['full_name'] = user['full_name']
            
            return jsonify({
                "success": True,
                "user": {
                    "id": str(user['id']),
                    "username": user['username'],
                    "email": user['email'],
                    "full_name": user['full_name'],
                    "role": user['role']
                }
            })
        except Exception as e:
            logger.error(f"Supabase login error: {e}")
            return jsonify({"error": str(e)}), 500
    
    # Mock login
    users = MOCK_DATABASE.get("rmc_users", [])
    user = None
    for u in users:
        if u['username'] == username_or_email or u['email'] == username_or_email:
            user = u
            break
    
    if not user:
        return jsonify({"error": "Invalid credentials"}), 401
    
    if not user['is_active']:
        return jsonify({"error": "Account is inactive"}), 401
    
    if not check_password_hash(user['password_hash'], password):
        return jsonify({"error": "Invalid credentials"}), 401
    
    # Set session
    session['user_id'] = user['id']
    session['username'] = user['username']
    session['role'] = user['role']
    session['full_name'] = user['full_name']
    
    return jsonify({
        "success": True,
        "user": {
            "id": user['id'],
            "username": user['username'],
            "email": user['email'],
            "full_name": user['full_name'],
            "role": user['role']
        },
        "mode": "mock"
    })

@app.route('/api/auth/register', methods=['POST'])
def api_register():
    # Rate limiting based on IP address
    client_ip = request.remote_addr
    if not check_rate_limit(f"register_{client_ip}", max_requests=3, window_seconds=3600):
        return jsonify({"error": "Too many registration attempts. Please try again later."}), 429
    
    data = request.json
    username = data.get('username')
    email = data.get('email')
    password = data.get('password')
    full_name = data.get('full_name')
    phone = data.get('phone')
    
    if not all([username, email, password, full_name]):
        return jsonify({"error": "Missing required fields"}), 400
    
    # Check if username or email already exists
    if SUPABASE_CLIENT:
        try:
            existing = SUPABASE_CLIENT.table("rmc_users").select("*").or_(f"username.eq.{username},email.eq.{email}").execute()
            if existing.data:
                return jsonify({"error": "Username or email already exists"}), 400
            
            # Create user
            password_hash = generate_password_hash(password)
            user_response = SUPABASE_CLIENT.table("rmc_users").insert({
                "username": username,
                "email": email,
                "password_hash": password_hash,
                "full_name": full_name,
                "role": "client",
                "phone": phone
            }).execute()
            
            return jsonify({"success": True, "user_id": str(user_response.data[0]['id'])})
        except Exception as e:
            logger.error(f"Supabase registration error: {e}")
            return jsonify({"error": str(e)}), 500
    
    # Mock registration
    users = MOCK_DATABASE.get("rmc_users", [])
    for u in users:
        if u['username'] == username or u['email'] == email:
            return jsonify({"error": "Username or email already exists"}), 400
    
    new_user = {
        "id": f"user-{len(users) + 3}",
        "username": username,
        "email": email,
        "password_hash": generate_password_hash(password),
        "full_name": full_name,
        "role": "client",
        "phone": phone or "",
        "is_active": True,
        "created_at": datetime.utcnow().isoformat()
    }
    MOCK_DATABASE["rmc_users"].append(new_user)
    save_db()   # ← persist so login survives server restart
    
    return jsonify({"success": True, "user_id": new_user['id'], "mode": "mock"})

@app.route('/api/auth/me', methods=['GET'])
def api_me():
    if 'user_id' not in session:
        return jsonify({"error": "Not authenticated"}), 401

    # Look up full user record to get email, phone, created_at
    uid = session['user_id']
    full_user = next((u for u in MOCK_DATABASE.get('rmc_users', []) if str(u.get('id')) == str(uid)), None)

    return jsonify({
        "user": {
            "id":         session['user_id'],
            "username":   session['username'],
            "role":       session['role'],
            "full_name":  session['full_name'],
            "email":      full_user.get('email', '')      if full_user else '',
            "phone":      full_user.get('phone', '')      if full_user else '',
            "created_at": full_user.get('created_at', '') if full_user else '',
        }
    })


@app.route('/rmc-portal')
def rmc_portal():
    # Check if user is logged in
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    # Check if user is a client
    if session.get('role') != 'client':
        return redirect(url_for('login'))
    
    return render_template('rmc_portal.html')

@app.route('/rmc-admin')
def rmc_admin():
    # Check if user is logged in
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    # Check if user is admin or manager
    if session.get('role') not in ['admin', 'manager']:
        return redirect(url_for('login'))
    
    return render_template('rmc_admin.html')

# ----------------- API Endpoints -----------------

@app.route('/api/founder', methods=['GET'])
def get_founder():
    if SUPABASE_CLIENT:
        try:
            response = SUPABASE_CLIENT.table("founder_ceo").select("*").limit(1).execute()
            if response.data:
                return jsonify(response.data[0])
        except Exception as e:
            logger.error(f"Supabase founder query error: {e}")
    
    # Return mock data as fallback
    return jsonify(MOCK_DATABASE["founder"])


@app.route('/api/plants', methods=['GET'])
def get_plants():
    if SUPABASE_CLIENT:
        try:
            response = SUPABASE_CLIENT.table("plants").select("*").execute()
            if response.data:
                return jsonify(response.data)
        except Exception as e:
            logger.error(f"Supabase plants query error: {e}")
            
    return jsonify(MOCK_DATABASE["plants"])


@app.route('/api/projects', methods=['GET'])
def get_projects():
    if SUPABASE_CLIENT:
        try:
            response = SUPABASE_CLIENT.table("projects").select("*").execute()
            if response.data:
                return jsonify(response.data)
        except Exception as e:
            logger.error(f"Supabase projects query error: {e}")
            
    return jsonify(MOCK_DATABASE["projects"])


@app.route('/api/contact', methods=['POST'])
def submit_contact():
    data = request.json or {}
    name = data.get('name')
    email = data.get('email')
    message = data.get('message')
    
    if not name or not email or not message:
        return jsonify({"error": "Missing required fields"}), 400
        
    if SUPABASE_CLIENT:
        try:
            SUPABASE_CLIENT.table("contact_submissions").insert({
                "name": name,
                "email": email,
                "message": message
            }).execute()
            return jsonify({"success": True, "message": "Message received via Supabase."})
        except Exception as e:
            logger.error(f"Supabase contact submission error: {e}")
            
    # Mock fallback submission
    MOCK_DATABASE["submissions"].append(data)
    logger.info(f"Local Mock Submission received: {data}")
    return jsonify({"success": True, "message": "Message submitted locally (Mock Mode)."})


@app.route('/api/subscribe', methods=['POST'])
def submit_subscribe():
    data = request.json or {}
    email = data.get('email')
    
    if not email:
        return jsonify({"error": "Email is required"}), 400
        
    if SUPABASE_CLIENT:
        try:
            SUPABASE_CLIENT.table("newsletter_subscribers").insert({
                "email": email
            }).execute()
            return jsonify({"success": True, "message": "Subscribed via Supabase."})
        except Exception as e:
            logger.error(f"Supabase newsletter subscription error: {e}")
            
    MOCK_DATABASE["newsletter"].append(email)
    logger.info(f"Local Mock Newsletter Subscription: {email}")
    return jsonify({"success": True, "message": "Subscribed locally (Mock Mode)."})


# ----------------- Protected Admin API Routes -----------------
# For mock mode or authentication bypass, we read standard payload fields. 
# Real Supabase admin uses JS SDK direct inserts with RLS, but these endpoints support alternate clients.

@app.route('/api/admin/update-plant', methods=['POST'])
def update_plant():
    data = request.json or {}
    plant_id = data.get('id')
    status = data.get('status')
    live_metrics = data.get('live_metrics')
    
    if not plant_id or not status:
        return jsonify({"error": "Missing plant ID or status"}), 400
        
    if SUPABASE_CLIENT:
        try:
            payload = {"status": status}
            if live_metrics is not None:
                payload["live_metrics"] = live_metrics
            payload["last_updated"] = "now()"
            
            SUPABASE_CLIENT.table("plants").update(payload).eq("id", plant_id).execute()
            return jsonify({"success": True})
        except Exception as e:
            logger.error(f"Supabase admin plant update error: {e}")
            return jsonify({"error": str(e)}), 500
            
    # Mock update
    for plant in MOCK_DATABASE["plants"]:
        if plant["id"] == plant_id:
            plant["status"] = status
            if live_metrics is not None:
                plant["live_metrics"] = live_metrics
            plant["last_updated"] = "Just now"
            return jsonify({"success": True, "mode": "mock"})
            
    return jsonify({"error": "Plant not found"}), 404


@app.route('/api/admin/update-project', methods=['POST'])
def update_project():
    data = request.json or {}
    project_id = data.get('id')
    progress = data.get('progress')
    
    if not project_id or progress is None:
        return jsonify({"error": "Missing project ID or progress value"}), 400
        
    if SUPABASE_CLIENT:
        try:
            SUPABASE_CLIENT.table("projects").update({"progress": int(progress)}).eq("id", project_id).execute()
            return jsonify({"success": True})
        except Exception as e:
            logger.error(f"Supabase admin project update error: {e}")
            return jsonify({"error": str(e)}), 500
            
    # Mock update
    for project in MOCK_DATABASE["projects"]:
        if project["id"] == project_id:
            project["progress"] = int(progress)
            return jsonify({"success": True, "mode": "mock"})
            
    return jsonify({"error": "Project not found"}), 404


# ----------------- RMC Module API Endpoints -----------------

@app.route('/api/rmc/grades', methods=['GET'])
def get_rmc_grades():
    if SUPABASE_CLIENT:
        try:
            response = SUPABASE_CLIENT.table("rmc_concrete_grades").select("*").eq("is_active", True).execute()
            if response.data:
                return jsonify(response.data)
        except Exception as e:
            logger.error(f"Supabase grades query error: {e}")
    return jsonify(MOCK_DATABASE["rmc_concrete_grades"])

@app.route('/api/rmc/clients', methods=['GET', 'POST'])
def rmc_clients():
    if request.method == 'GET':
        if SUPABASE_CLIENT:
            try:
                response = SUPABASE_CLIENT.table("rmc_clients").select("*").execute()
                if response.data:
                    return jsonify(response.data)
            except Exception as e:
                logger.error(f"Supabase clients query error: {e}")
        return jsonify(MOCK_DATABASE["rmc_clients"])
    
    elif request.method == 'POST':
        data = request.json
        if not data.get('company_name') or not data.get('email') or not data.get('phone'):
            return jsonify({"error": "Missing required fields"}), 400
        
        if SUPABASE_CLIENT:
            try:
                response = SUPABASE_CLIENT.table("rmc_clients").insert({
                    "company_name": data['company_name'],
                    "contact_person": data.get('contact_person', ''),
                    "email": data['email'],
                    "phone": data['phone'],
                    "billing_address": data.get('billing_address', ''),
                    "shipping_address": data.get('shipping_address', ''),
                    "gst_number": data.get('gst_number', ''),
                    "credit_limit": data.get('credit_limit', 0)
                }).execute()
                return jsonify({"success": True, "client": response.data[0]})
            except Exception as e:
                logger.error(f"Supabase client insert error: {e}")
        
        # Mock insert
        new_client = {
            "id": f"client-{len(MOCK_DATABASE['rmc_clients']) + 1}",
            **data,
            "current_balance": 0.00,
            "is_active": True
        }
        MOCK_DATABASE["rmc_clients"].append(new_client)
        return jsonify({"success": True, "client": new_client, "mode": "mock"})

@app.route('/api/rmc/orders', methods=['GET', 'POST'])
def rmc_orders():
    if request.method == 'GET':
        client_id = request.args.get('client_id')
        
        # Check authentication and role
        user_role = session.get('role')
        user_id = session.get('user_id')
        
        if SUPABASE_CLIENT:
            try:
                query = SUPABASE_CLIENT.table("rmc_orders").select("*")
                
                # Filter by role
                if user_role == 'client' and user_id:
                    query = query.eq("user_id", user_id)
                elif client_id:
                    query = query.eq("client_id", client_id)
                
                response = query.execute()
                if response.data:
                    return jsonify(response.data)
            except Exception as e:
                logger.error(f"Supabase orders query error: {e}")
        
        # Mock
        orders = MOCK_DATABASE["rmc_orders"]
        
        # Filter by role
        if user_role == 'client' and user_id:
            orders = [o for o in orders if o.get('user_id') == user_id]
        elif client_id:
            orders = [o for o in orders if o.get('client_id') == client_id]
        
        return jsonify(orders)
    
    elif request.method == 'POST':
        data = request.json
        if not data.get('customer_name') or not data.get('items'):
            return jsonify({"error": "Missing customer_name or items"}), 400
        
        # Check authentication
        user_id = session.get('user_id')
        user_role = session.get('role')
        
        if not user_id:
            return jsonify({"error": "Not authenticated"}), 401
        
        # Calculate total
        total_amount = 0
        for item in data['items']:
            total_amount += item.get('subtotal', 0)
        
        order_number = f"RMC-{datetime.now().strftime('%Y%m%d')}-{len(MOCK_DATABASE['rmc_orders']) + 1:04d}"
        
        if SUPABASE_CLIENT:
            try:
                # Create order
                order_response = SUPABASE_CLIENT.table("rmc_orders").insert({
                    "order_number": order_number,
                    "user_id": user_id,
                    "customer_name": data['customer_name'],
                    "phone": data.get('phone'),
                    "delivery_date": data.get('delivery_date'),
                    "delivery_address": data.get('delivery_address'),
                    "status": "Pending",
                    "total_amount": total_amount,
                    "notes": data.get('notes', '')
                }).execute()
                order_id = order_response.data[0]['id']
                
                # Create order items
                for item in data['items']:
                    SUPABASE_CLIENT.table("rmc_order_items").insert({
                        "order_id": order_id,
                        "grade_id": item['grade_id'],
                        "quantity_cubic_meters": item['quantity'],
                        "unit_price": item['unit_price'],
                        "subtotal": item['subtotal']
                    }).execute()
                
                return jsonify({"success": True, "order_id": order_id, "order_number": order_number})
            except Exception as e:
                logger.error(f"Supabase order insert error: {e}")
                return jsonify({"error": str(e)}), 500
        
        # Mock insert
        new_order = {
            "id": f"order-{len(MOCK_DATABASE['rmc_orders']) + 1}",
            "order_number": order_number,
            "user_id": user_id,
            "customer_name": data['customer_name'],
            "phone": data.get('phone'),
            "order_date": datetime.now().isoformat(),
            "delivery_date": data.get('delivery_date'),
            "delivery_address": data.get('delivery_address'),
            "status": "Pending",
            "total_amount": total_amount,
            "notes": data.get('notes', ''),
            "items": data['items']
        }
        MOCK_DATABASE["rmc_orders"].append(new_order)
        return jsonify({"success": True, "order_id": new_order['id'], "order_number": order_number, "mode": "mock"})

@app.route('/api/rmc/orders/<order_id>/approve', methods=['POST'])
def approve_order(order_id):
    data = request.json
    approved_by = data.get('approved_by', 'Admin')
    
    # Find the order first
    order = None
    if SUPABASE_CLIENT:
        try:
            response = SUPABASE_CLIENT.table("rmc_orders").select("*").eq("id", order_id).execute()
            if response.data:
                order = response.data[0]
        except Exception as e:
            logger.error(f"Supabase order query error: {e}")
    else:
        for o in MOCK_DATABASE["rmc_orders"]:
            if o['id'] == order_id:
                order = o
                break
    
    if not order:
        return jsonify({"error": "Order not found"}), 404
    
    # Update order status
    if SUPABASE_CLIENT:
        try:
            SUPABASE_CLIENT.table("rmc_orders").update({
                "status": "Approved",
                "approved_by": approved_by,
                "approved_at": datetime.now().isoformat()
            }).eq("id", order_id).execute()
        except Exception as e:
            logger.error(f"Supabase order approve error: {e}")
            return jsonify({"error": str(e)}), 500
    else:
        for o in MOCK_DATABASE["rmc_orders"]:
            if o['id'] == order_id:
                o['status'] = "Approved"
                o['approved_by'] = approved_by
                o['approved_at'] = datetime.now().isoformat()
                order = o
                break
    
    # Generate invoice automatically
    invoice_number = f"INV-{datetime.now().strftime('%Y%m%d')}-{len(MOCK_DATABASE.get('rmc_invoices', [])) + 1:04d}"
    
    if SUPABASE_CLIENT:
        try:
            # Create invoice
            invoice_response = SUPABASE_CLIENT.table("rmc_invoices").insert({
                "invoice_number": invoice_number,
                "order_id": order_id,
                "invoice_date": datetime.now().date().isoformat(),
                "due_date": (datetime.now() + timedelta(days=30)).date().isoformat(),
                "subtotal": order.get('total_amount', 0),
                "tax_amount": 0,
                "total_amount": order.get('total_amount', 0),
                "status": "Pending",
                "notes": f"Auto-generated invoice for order {order.get('order_number')}"
            }).execute()
            invoice_id = invoice_response.data[0]['id']
        except Exception as e:
            logger.error(f"Supabase invoice creation error: {e}")
    else:
        # Mock invoice creation
        new_invoice = {
            "id": f"invoice-{len(MOCK_DATABASE.get('rmc_invoices', [])) + 1}",
            "invoice_number": invoice_number,
            "order_id": order_id,
            "invoice_date": datetime.now().date().isoformat(),
            "due_date": (datetime.now() + timedelta(days=30)).date().isoformat(),
            "subtotal": order.get('total_amount', 0),
            "tax_amount": 0,
            "total_amount": order.get('total_amount', 0),
            "status": "Pending",
            "notes": f"Auto-generated invoice for order {order.get('order_number')}"
        }
        MOCK_DATABASE.setdefault("rmc_invoices", []).append(new_invoice)
        invoice_id = new_invoice['id']
    
    return jsonify({
        "success": True,
        "invoice_id": invoice_id,
        "invoice_number": invoice_number,
        "mode": "mock" if not SUPABASE_CLIENT else "supabase"
    })

@app.route('/api/rmc/orders/<order_id>', methods=['PUT'])
def update_order(order_id):
    data = request.json
    status = data.get('status')
    
    if not status:
        return jsonify({"error": "Missing status"}), 400
    
    if SUPABASE_CLIENT:
        try:
            SUPABASE_CLIENT.table("rmc_orders").update({
                "status": status,
                "updated_at": datetime.now().isoformat()
            }).eq("id", order_id).execute()
            return jsonify({"success": True})
        except Exception as e:
            logger.error(f"Supabase order update error: {e}")
            return jsonify({"error": str(e)}), 500
    
    # Mock update
    for order in MOCK_DATABASE["rmc_orders"]:
        if order['id'] == order_id:
            order['status'] = status
            order['updated_at'] = datetime.now().isoformat()
            return jsonify({"success": True, "mode": "mock"})
    
    return jsonify({"error": "Order not found"}), 404

@app.route('/api/rmc/invoices', methods=['GET', 'POST'])
def rmc_invoices():
    if request.method == 'GET':
        order_id = request.args.get('order_id')
        if SUPABASE_CLIENT:
            try:
                query = SUPABASE_CLIENT.table("rmc_invoices").select("*")
                if order_id:
                    query = query.eq("order_id", order_id)
                response = query.execute()
                if response.data:
                    return jsonify(response.data)
            except Exception as e:
                logger.error(f"Supabase invoices query error: {e}")
        
        invoices = MOCK_DATABASE["rmc_invoices"]
        if order_id:
            invoices = [i for i in invoices if i.get('order_id') == order_id]
        return jsonify(invoices)
    
    elif request.method == 'POST':
        data = request.json
        if not data.get('order_id') or not data.get('client_id'):
            return jsonify({"error": "Missing order_id or client_id"}), 400
        
        invoice_number = f"INV-{datetime.now().strftime('%Y%m%d')}-{len(MOCK_DATABASE['rmc_invoices']) + 1:04d}"
        due_date = (datetime.now() + timedelta(days=30)).date()
        
        if SUPABASE_CLIENT:
            try:
                response = SUPABASE_CLIENT.table("rmc_invoices").insert({
                    "invoice_number": invoice_number,
                    "order_id": data['order_id'],
                    "client_id": data['client_id'],
                    "due_date": due_date.isoformat(),
                    "subtotal": data['subtotal'],
                    "tax_amount": data.get('tax_amount', 0),
                    "total_amount": data['total_amount'],
                    "status": "Sent",
                    "payment_terms": data.get('payment_terms', 'Net 30 days')
                }).execute()
                return jsonify({"success": True, "invoice": response.data[0]})
            except Exception as e:
                logger.error(f"Supabase invoice insert error: {e}")
                return jsonify({"error": str(e)}), 500
        
        # Mock insert
        new_invoice = {
            "id": f"invoice-{len(MOCK_DATABASE['rmc_invoices']) + 1}",
            "invoice_number": invoice_number,
            "order_id": data['order_id'],
            "client_id": data['client_id'],
            "invoice_date": datetime.now().date().isoformat(),
            "due_date": due_date.isoformat(),
            "subtotal": data['subtotal'],
            "tax_amount": data.get('tax_amount', 0),
            "total_amount": data['total_amount'],
            "status": "Sent",
            "payment_terms": data.get('payment_terms', 'Net 30 days')
        }
        MOCK_DATABASE["rmc_invoices"].append(new_invoice)
        return jsonify({"success": True, "invoice": new_invoice, "mode": "mock"})

@app.route('/api/rmc/payments', methods=['GET', 'POST'])
def rmc_payments():
    if request.method == 'GET':
        client_id = request.args.get('client_id')
        if SUPABASE_CLIENT:
            try:
                query = SUPABASE_CLIENT.table("rmc_payment_records").select("*")
                if client_id:
                    query = query.eq("client_id", client_id)
                response = query.execute()
                if response.data:
                    return jsonify(response.data)
            except Exception as e:
                logger.error(f"Supabase payments query error: {e}")
        
        payments = MOCK_DATABASE["rmc_payments"]
        if client_id:
            payments = [p for p in payments if p.get('client_id') == client_id]
        return jsonify(payments)
    
    elif request.method == 'POST':
        data = request.json
        if not data.get('client_id') or not data.get('amount'):
            return jsonify({"error": "Missing client_id or amount"}), 400
        
        payment_number = f"PAY-{datetime.now().strftime('%Y%m%d')}-{len(MOCK_DATABASE['rmc_payments']) + 1:04d}"
        
        if SUPABASE_CLIENT:
            try:
                response = SUPABASE_CLIENT.table("rmc_payment_records").insert({
                    "payment_number": payment_number,
                    "invoice_id": data.get('invoice_id'),
                    "client_id": data['client_id'],
                    "amount": data['amount'],
                    "payment_method": data.get('payment_method', 'Bank Transfer'),
                    "reference_number": data.get('reference_number', ''),
                    "notes": data.get('notes', '')
                }).execute()
                return jsonify({"success": True, "payment": response.data[0]})
            except Exception as e:
                logger.error(f"Supabase payment insert error: {e}")
                return jsonify({"error": str(e)}), 500
        
        # Mock insert
        new_payment = {
            "id": f"payment-{len(MOCK_DATABASE['rmc_payments']) + 1}",
            "payment_number": payment_number,
            "invoice_id": data.get('invoice_id'),
            "client_id": data['client_id'],
            "payment_date": datetime.now().date().isoformat(),
            "amount": data['amount'],
            "payment_method": data.get('payment_method', 'Bank Transfer'),
            "reference_number": data.get('reference_number', ''),
            "notes": data.get('notes', '')
        }
        MOCK_DATABASE["rmc_payments"].append(new_payment)
        return jsonify({"success": True, "payment": new_payment, "mode": "mock"})

@app.route('/api/rmc/export/orders', methods=['GET'])
def export_orders_excel():
    client_id = request.args.get('client_id')
    
    # Get data
    if SUPABASE_CLIENT:
        try:
            query = SUPABASE_CLIENT.table("rmc_orders").select("*")
            if client_id:
                query = query.eq("client_id", client_id)
            response = query.execute()
            orders = response.data if response.data else []
        except Exception as e:
            logger.error(f"Supabase export error: {e}")
            orders = MOCK_DATABASE["rmc_orders"]
    else:
        orders = MOCK_DATABASE["rmc_orders"]
        if client_id:
            orders = [o for o in orders if o.get('client_id') == client_id]
    
    # Create Excel workbook
    wb = Workbook()
    ws = wb.active
    ws.title = "Orders"
    
    # Headers
    headers = ["Order Number", "Client ID", "Order Date", "Delivery Date", "Status", "Total Amount", "Notes"]
    ws.append(headers)
    
    # Style headers
    for col in range(1, len(headers) + 1):
        cell = ws.cell(row=1, column=col)
        cell.font = Font(bold=True, color="FFFFFF")
        cell.fill = PatternFill(start_color="4472C4", end_color="4472C4", fill_type="solid")
        cell.alignment = Alignment(horizontal="center")
    
    # Data rows
    for order in orders:
        ws.append([
            order.get('order_number', ''),
            order.get('client_id', ''),
            order.get('order_date', ''),
            order.get('delivery_date', ''),
            order.get('status', ''),
            order.get('total_amount', 0),
            order.get('notes', '')
        ])
    
    # Save to bytes
    from io import BytesIO
    output = BytesIO()
    wb.save(output)
    output.seek(0)
    
    response = make_response(output.getvalue())
    response.headers['Content-Disposition'] = 'attachment; filename=rmc_orders_export.xlsx'
    response.headers['Content-Type'] = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    return response

@app.route('/api/rmc/invoices/<invoice_id>/pdf', methods=['GET'])
def generate_invoice_pdf(invoice_id):
    from io import BytesIO
    import os
    from reportlab.lib.units import inch
    from reportlab.platypus import Image, Table, TableStyle, Flowable
    from reportlab.lib import colors
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.platypus import Paragraph, Spacer, SimpleDocTemplate
    from reportlab.lib.enums import TA_LEFT, TA_RIGHT, TA_CENTER
    from reportlab.platypus import PageTemplate, Frame
    from reportlab.lib.pagesizes import A4
    
    try:
        # Find the invoice
        invoice = None
        order = None
        
        if SUPABASE_CLIENT:
            try:
                inv_response = SUPABASE_CLIENT.table("rmc_invoices").select("*").eq("id", invoice_id).execute()
                if inv_response.data:
                    invoice = inv_response.data[0]
                    order_response = SUPABASE_CLIENT.table("rmc_orders").select("*").eq("id", invoice['order_id']).execute()
                    if order_response.data:
                        order = order_response.data[0]
            except Exception as e:
                logger.error(f"Supabase invoice query error: {e}")
        else:
            for inv in MOCK_DATABASE.get("rmc_invoices", []):
                if inv['id'] == invoice_id:
                    invoice = inv
                    for ord in MOCK_DATABASE.get("rmc_orders", []):
                        if ord['id'] == invoice['order_id']:
                            order = ord
                            break
                    break
        
        if not invoice or not order:
            logger.error(f"Invoice or order not found for invoice_id: {invoice_id}")
            return jsonify({"error": "Invoice or order not found"}), 404
        
        # Create PDF
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=20, bottomMargin=20, leftMargin=20, rightMargin=20)
        elements = []
        styles = getSampleStyleSheet()
        
        # Custom styles for overlay text
        invoice_title_style = ParagraphStyle(
            'InvoiceTitle',
            parent=styles['Heading1'],
            fontSize=16,
            textColor=colors.black,
            spaceAfter=0,
            alignment=TA_RIGHT
        )
        
        normal_style = ParagraphStyle(
            'CustomNormal',
            parent=styles['Normal'],
            fontSize=10,
            textColor=colors.black,
            spaceAfter=0,
            alignment=TA_LEFT
        )
        
        bold_style = ParagraphStyle(
            'Bold',
            parent=styles['Normal'],
            fontSize=10,
            textColor=colors.black,
            fontName='Helvetica-Bold',
            spaceAfter=0,
            alignment=TA_LEFT
        )
        
        # Add invoice template as background image
        sheet_path = os.path.join('static', 'images', 'invoice_template.jpg')
        
        def on_first_page(canvas, doc):
            if os.path.exists(sheet_path):
                try:
                    canvas.drawImage(sheet_path, 0, 0, width=A4[0], height=A4[1], preserveAspectRatio=True)
                except Exception as e:
                    logger.error(f"Error drawing invoice template: {e}")
        
        # Create a custom flowable for absolute positioning
        class AbsolutePosition(Flowable):
            def __init__(self, x, y, text, style):
                Flowable.__init__(self)
                self.x = x
                self.y = y
                self.text = text
                self.style = style
            
            def wrap(self, availWidth, availHeight):
                return (0, 0)
            
            def draw(self):
                self.canv.saveState()
                self.canv.setFont(self.style.fontName, self.style.fontSize)
                self.canv.setFillColor(self.style.textColor)
                self.canv.drawString(self.x, self.y, self.text)
                self.canv.restoreState()
        
        # Add text overlays at specific positions (coordinates in points)
        # These coordinates need to match the template layout
        text_overlays = [
            # Invoice No - top right
            (450, 780, invoice.get('invoice_number', ''), bold_style),
            # Invoice Date - top right below invoice no
            (450, 760, invoice.get('invoice_date', ''), normal_style),
            # Due Date - top right below date
            (450, 740, invoice.get('due_date', ''), normal_style),
            # Order No - top right below due date
            (450, 720, order.get('order_number', ''), normal_style),
            # Company Name - left side
            (80, 680, order.get('customer_name', ''), bold_style),
            # Address - below company
            (80, 660, order.get('delivery_address', ''), normal_style),
            # Phone - below address
            (80, 640, order.get('phone', ''), normal_style),
            # Total Amount - bottom right
            (450, 200, f"₹{invoice.get('total_amount', 0):,.2f}", bold_style),
        ]
        
        for x, y, text, style in text_overlays:
            elements.append(AbsolutePosition(x, y, text, style))
        
        # Build PDF with background image
        doc.build(elements, onFirstPage=on_first_page)
        buffer.seek(0)
        
        response = make_response(buffer.getvalue())
        response.headers['Content-Disposition'] = f'attachment; filename=invoice_{invoice["invoice_number"]}.pdf'
        response.headers['Content-Type'] = 'application/pdf'
        return response
    except Exception as e:
        logger.error(f"Error generating PDF: {e}")
        return jsonify({"error": f"Error generating PDF: {str(e)}"}), 500

@app.route('/api/rmc/export/invoices', methods=['GET'])
def export_invoices_excel():
    if SUPABASE_CLIENT:
        try:
            response = SUPABASE_CLIENT.table("rmc_invoices").select("*").execute()
            invoices = response.data if response.data else []
        except Exception as e:
            logger.error(f"Supabase export error: {e}")
            invoices = MOCK_DATABASE["rmc_invoices"]
    else:
        invoices = MOCK_DATABASE["rmc_invoices"]
    
    wb = Workbook()
    ws = wb.active
    ws.title = "Invoices"
    
    headers = ["Invoice Number", "Order ID", "Client ID", "Invoice Date", "Due Date", "Subtotal", "Tax", "Total", "Status"]
    ws.append(headers)
    
    for col in range(1, len(headers) + 1):
        cell = ws.cell(row=1, column=col)
        cell.font = Font(bold=True, color="FFFFFF")
        cell.fill = PatternFill(start_color="4472C4", end_color="4472C4", fill_type="solid")
        cell.alignment = Alignment(horizontal="center")
    
    for invoice in invoices:
        ws.append([
            invoice.get('invoice_number', ''),
            invoice.get('order_id', ''),
            invoice.get('client_id', ''),
            invoice.get('invoice_date', ''),
            invoice.get('due_date', ''),
            invoice.get('subtotal', 0),
            invoice.get('tax_amount', 0),
            invoice.get('total_amount', 0),
            invoice.get('status', '')
        ])
    
    from io import BytesIO
    output = BytesIO()
    wb.save(output)
    output.seek(0)
    
    response = make_response(output.getvalue())
    response.headers['Content-Disposition'] = 'attachment; filename=rmc_invoices_export.xlsx'
    response.headers['Content-Type'] = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    return response

# Manual Billing Module
@app.route('/api/manual-billing', methods=['GET', 'POST'])
def manual_billing():
    if request.method == 'GET':
        if SUPABASE_CLIENT:
            try:
                response = SUPABASE_CLIENT.table("manual_billing").select("*").execute()
                billing_records = response.data if response.data else []
            except Exception as e:
                logger.error(f"Supabase billing fetch error: {e}")
                billing_records = MOCK_DATABASE.get("manual_billing", [])
        else:
            billing_records = MOCK_DATABASE.get("manual_billing", [])
        return jsonify({"success": True, "data": billing_records})
    
    elif request.method == 'POST':
        data = request.json
        required_fields = ['company_name', 'phone', 'address', 'date', 'time', 'vehicle_number', 'driver_name', 'unloading_time', 'grade', 'cubic_meters', 'loading_time', 'rate_per_cubic']
        
        for field in required_fields:
            if field not in data or not data[field]:
                return jsonify({"error": f"Missing required field: {field}"}), 400
        
        billing_record = {
            "id": f"bill-{len(MOCK_DATABASE.get('manual_billing', [])) + 1}",
            "company_name": data['company_name'],
            "phone": data['phone'],
            "address": data['address'],
            "date": data['date'],
            "time": data['time'],
            "vehicle_number": data['vehicle_number'],
            "driver_name": data['driver_name'],
            "unloading_time": data['unloading_time'],
            "grade": data['grade'],
            "cubic_meters": data['cubic_meters'],
            "loading_time": data['loading_time'],
            "rate_per_cubic": data['rate_per_cubic'],
            "total_amount": data.get('total_amount', 0),
            "advance_amount": data.get('advance_amount', 0),
            "balance_amount": data.get('balance_amount', 0),
            "created_at": datetime.now().isoformat(),
            "created_by": session.get('username', 'system')
        }
        
        if SUPABASE_CLIENT:
            try:
                response = SUPABASE_CLIENT.table("manual_billing").insert(billing_record).execute()
                if response.data:
                    billing_record = response.data[0]
            except Exception as e:
                logger.error(f"Supabase billing insert error: {e}")
        else:
            MOCK_DATABASE.setdefault("manual_billing", []).append(billing_record)
            save_db()  # Persist to disk
        
        return jsonify({"success": True, "data": billing_record})

@app.route('/api/manual-billing/<billing_id>', methods=['PUT', 'DELETE'])
def manual_billing_detail(billing_id):
    if request.method == 'PUT':
        data = request.json
        
        if SUPABASE_CLIENT:
            try:
                SUPABASE_CLIENT.table("manual_billing").update(data).eq("id", billing_id).execute()
            except Exception as e:
                logger.error(f"Supabase billing update error: {e}")
        else:
            for record in MOCK_DATABASE.get("manual_billing", []):
                if record['id'] == billing_id:
                    record.update(data)
                    break
            save_db()  # Persist to disk
        
        return jsonify({"success": True})
    
    elif request.method == 'DELETE':
        if SUPABASE_CLIENT:
            try:
                SUPABASE_CLIENT.table("manual_billing").delete().eq("id", billing_id).execute()
            except Exception as e:
                logger.error(f"Supabase billing delete error: {e}")
        else:
            MOCK_DATABASE["manual_billing"] = [r for r in MOCK_DATABASE.get("manual_billing", []) if r['id'] != billing_id]
            save_db()  # Persist to disk
        
        return jsonify({"success": True})

@app.route('/api/manual-billing/<billing_id>/pdf', methods=['GET'])
def manual_billing_pdf(billing_id):
    from io import BytesIO
    from reportlab.lib.pagesizes import A4
    from reportlab.lib import colors
    from reportlab.pdfgen import canvas as pdf_canvas
    from reportlab.lib.units import mm
    import os

    try:
        billing_record = None

        if SUPABASE_CLIENT:
            try:
                response = SUPABASE_CLIENT.table("manual_billing").select("*").eq("id", billing_id).execute()
                if response.data:
                    billing_record = response.data[0]
            except Exception as e:
                logger.error(f"Supabase billing fetch error: {e}")
        else:
            for record in MOCK_DATABASE.get("manual_billing", []):
                if record['id'] == billing_id:
                    billing_record = record
                    break

        if not billing_record:
            return jsonify({"error": "Billing record not found"}), 404

        buffer = BytesIO()
        W, H = A4  # 595.28 x 841.89 points
        c = pdf_canvas.Canvas(buffer, pagesize=A4)

        # ── COLORS ──────────────────────────────────────────────
        GOLD        = colors.HexColor('#D4AF37')
        DARK_GOLD   = colors.HexColor('#B8962E')
        BLACK       = colors.HexColor('#1a1a1a')
        WHITE       = colors.white
        LIGHT_GRAY  = colors.HexColor('#f5f5f5')
        MID_GRAY    = colors.HexColor('#e0e0e0')
        TEXT_GRAY   = colors.HexColor('#555555')

        # ── HELPER ───────────────────────────────────────────────
        def draw_text(x, y, text, font='Helvetica', size=9, color=BLACK):
            c.setFont(font, size)
            c.setFillColor(color)
            c.drawString(x, y, str(text))

        def draw_right_text(x, y, text, font='Helvetica', size=9, color=BLACK):
            c.setFont(font, size)
            c.setFillColor(color)
            c.drawRightString(x, y, str(text))

        def draw_rect(x, y, w, h, fill_color=None, stroke_color=None, stroke_width=0.5):
            c.setLineWidth(stroke_width)
            if fill_color:
                c.setFillColor(fill_color)
            if stroke_color:
                c.setStrokeColor(stroke_color)
            if fill_color and stroke_color:
                c.rect(x, y, w, h, fill=1, stroke=1)
            elif fill_color:
                c.rect(x, y, w, h, fill=1, stroke=0)
            elif stroke_color:
                c.rect(x, y, w, h, fill=0, stroke=1)

        # ════════════════════════════════════════════════════════
        # SECTION 1 — TOP GOLD BANNER (logo box + company info)
        # ════════════════════════════════════════════════════════
        banner_h = 100
        banner_y = H - banner_h

        # Full gold banner background
        draw_rect(0, banner_y, W, banner_h, fill_color=GOLD)

        # Black logo box (left side)
        logo_box_w = 90
        logo_box_h = 76
        logo_box_x = 18
        logo_box_y = banner_y + (banner_h - logo_box_h) / 2
        draw_rect(logo_box_x, logo_box_y, logo_box_w, logo_box_h, fill_color=BLACK)

        # Draw logo image inside black box
        logo_path = os.path.join('static', 'images', 'logo.png')
        if os.path.exists(logo_path):
            try:
                c.drawImage(logo_path, logo_box_x + 5, logo_box_y + 5,
                            width=logo_box_w - 10, height=logo_box_h - 10,
                            preserveAspectRatio=True, mask='auto')
            except Exception as e:
                logger.error(f"Logo draw error: {e}")

        # ── White section to the right of gold banner (company + proprietor)
        white_section_x = logo_box_x + logo_box_w + 16
        white_section_y = banner_y
        white_section_w = W - white_section_x - 10

        # Company name + tagline (left of white section)
        company_x = white_section_x
        company_mid_y = banner_y + banner_h / 2

        draw_text(company_x, company_mid_y + 18, "R SUNDARAM & CO",
                  font='Helvetica-Bold', size=16, color=BLACK)
        draw_text(company_x, company_mid_y + 4, "STRONG ROADS  BUILD TO LAST",
                  font='Helvetica', size=8, color=BLACK)
        draw_text(company_x, company_mid_y - 10, "READYMIX CONCRETE",
                  font='Helvetica', size=8, color=BLACK)

        # Proprietor info (right side of banner)
        prop_x = W - 170
        prop_y = banner_y + 72
        draw_text(prop_x, prop_y,      "Proprietor",        font='Helvetica',      size=8,  color=BLACK)
        draw_text(prop_x, prop_y - 14, "S MAGHESH",         font='Helvetica-Bold', size=12, color=BLACK)
        draw_text(prop_x, prop_y - 27, "\u25a0 9940270304",   font='Helvetica',      size=8,  color=BLACK)
        draw_text(prop_x, prop_y - 38, "\u25a0 rsundaram&co@gmail.com", font='Helvetica', size=8, color=BLACK)
        draw_text(prop_x, prop_y - 49, "\u25a0 Quarry Rd, Tiruneermalai", font='Helvetica', size=8, color=BLACK)
        draw_text(prop_x, prop_y - 60, "Chennai, Tamil Nadu 600132", font='Helvetica', size=8, color=BLACK)

        # ════════════════════════════════════════════════════════
        # SECTION 2 — THIN DARK GOLD SEPARATOR LINE
        # ════════════════════════════════════════════════════════
        sep_y = banner_y - 3
        c.setStrokeColor(DARK_GOLD)
        c.setLineWidth(2)
        c.line(0, sep_y, W, sep_y)

        # ════════════════════════════════════════════════════════
        # SECTION 3 — DELIVERY CHALLAN TITLE
        # ════════════════════════════════════════════════════════
        title_y = sep_y - 38
        c.setFont('Helvetica-Bold', 22)
        c.setFillColor(GOLD)
        title_text = "DELIVERY CHALLAN"
        title_w = c.stringWidth(title_text, 'Helvetica-Bold', 22)
        c.drawString((W - title_w) / 2, title_y, title_text)

        # Underline
        c.setStrokeColor(GOLD)
        c.setLineWidth(1.5)
        underline_x = (W - title_w) / 2
        c.line(underline_x, title_y - 4, underline_x + title_w, title_y - 4)

        # ════════════════════════════════════════════════════════
        # SECTION 4 — BILL TO / CHALLAN DETAILS (two columns)
        # ════════════════════════════════════════════════════════
        info_top_y = title_y - 30
        col_left_x  = 30
        col_right_x = W / 2 + 10

        # "Bill To" label
        draw_text(col_left_x, info_top_y, "Bill To", font='Helvetica-Bold', size=9, color=TEXT_GRAY)
        # Bill To values
        r = billing_record
        draw_text(col_left_x, info_top_y - 14, "Company:", font='Helvetica-Bold', size=9, color=BLACK)
        draw_text(col_left_x + 55, info_top_y - 14, r.get('company_name', ''), font='Helvetica', size=9, color=BLACK)
        draw_text(col_left_x, info_top_y - 26, "Phone:",   font='Helvetica-Bold', size=9, color=BLACK)
        draw_text(col_left_x + 55, info_top_y - 26, str(r.get('phone', '')), font='Helvetica', size=9, color=BLACK)
        draw_text(col_left_x, info_top_y - 38, "Address:", font='Helvetica-Bold', size=9, color=BLACK)
        draw_text(col_left_x + 55, info_top_y - 38, str(r.get('address', '')), font='Helvetica', size=9, color=BLACK)

        # "Challan Details" label
        draw_text(col_right_x, info_top_y, "Challan Details", font='Helvetica-Bold', size=9, color=TEXT_GRAY)
        draw_text(col_right_x, info_top_y - 14, "Challan No:", font='Helvetica-Bold', size=9, color=BLACK)
        draw_text(col_right_x + 65, info_top_y - 14, str(r.get('id', '')), font='Helvetica', size=9, color=BLACK)
        draw_text(col_right_x, info_top_y - 26, "Date:", font='Helvetica-Bold', size=9, color=BLACK)
        draw_text(col_right_x + 65, info_top_y - 26, str(r.get('date', '')), font='Helvetica', size=9, color=BLACK)
        draw_text(col_right_x, info_top_y - 38, "Time:", font='Helvetica-Bold', size=9, color=BLACK)
        draw_text(col_right_x + 65, info_top_y - 38, str(r.get('time', '')), font='Helvetica', size=9, color=BLACK)

        # Horizontal rule below info section
        rule_y = info_top_y - 55
        c.setStrokeColor(MID_GRAY)
        c.setLineWidth(0.5)
        c.line(30, rule_y, W - 30, rule_y)

        # ════════════════════════════════════════════════════════
        # SECTION 5 — DETAILS TABLE
        # ════════════════════════════════════════════════════════
        table_top_y  = rule_y - 8
        table_left   = 30
        table_right  = W - 30
        table_width  = table_right - table_left
        col1_w       = table_width * 0.40   # Field column
        col2_w       = table_width * 0.60   # Details column
        row_h        = 26
        header_h     = 26

        # Table header row (gold background)
        draw_rect(table_left, table_top_y - header_h, table_width, header_h, fill_color=GOLD)
        draw_text(table_left + 10, table_top_y - header_h + 8, "Field",   font='Helvetica-Bold', size=9, color=BLACK)
        draw_text(table_left + col1_w + 10, table_top_y - header_h + 8, "Details", font='Helvetica-Bold', size=9, color=BLACK)

        # Table rows
        rows = [
            ("Vehicle Number",  str(r.get('vehicle_number', ''))),
            ("Driver Name",     str(r.get('driver_name', ''))),
            ("Grade",           str(r.get('grade', ''))),
            ("Quantity (m\u00b3)", str(r.get('cubic_meters', ''))),
            ("Rate per m\u00b3",   f"Rs. {float(r.get('rate_per_cubic', 0)):.2f}"),
            ("Loading Time",    str(r.get('loading_time', ''))),
            ("Unloading Time",  str(r.get('unloading_time', ''))),
        ]

        row_y = table_top_y - header_h
        for i, (field, detail) in enumerate(rows):
            row_bg = LIGHT_GRAY if i % 2 == 0 else WHITE
            draw_rect(table_left, row_y - row_h, table_width, row_h, fill_color=row_bg, stroke_color=MID_GRAY, stroke_width=0.4)
            # Vertical divider
            c.setStrokeColor(MID_GRAY)
            c.setLineWidth(0.4)
            c.line(table_left + col1_w, row_y - row_h, table_left + col1_w, row_y)
            draw_text(table_left + 10, row_y - row_h + 8, field,  font='Helvetica',      size=9, color=BLACK)
            draw_text(table_left + col1_w + 10, row_y - row_h + 8, detail, font='Helvetica', size=9, color=BLACK)
            row_y -= row_h

        # ════════════════════════════════════════════════════════
        # SECTION 6 — AMOUNTS SUMMARY (right-aligned)
        # ════════════════════════════════════════════════════════
        amt_top_y    = row_y - 20
        amt_right_x  = W - 30
        amt_label_x  = W - 200
        amt_val_x    = W - 30
        line_h       = 22

        total   = float(r.get('total_amount', 0))
        advance = float(r.get('advance_amount', 0))
        balance = float(r.get('balance_amount', 0))

        # Total Amount
        draw_text(amt_label_x, amt_top_y, "Total Amount:", font='Helvetica', size=10, color=BLACK)
        draw_right_text(amt_val_x, amt_top_y, f"Rs. {total:,.2f}", font='Helvetica-Bold', size=10, color=BLACK)

        # Advance Given
        draw_text(amt_label_x, amt_top_y - line_h, "Advance Given:", font='Helvetica', size=10, color=BLACK)
        draw_right_text(amt_val_x, amt_top_y - line_h, f"Rs. {advance:,.2f}", font='Helvetica', size=10, color=BLACK)

        # Gold divider line
        c.setStrokeColor(GOLD)
        c.setLineWidth(1.2)
        c.line(amt_label_x, amt_top_y - line_h - 8, amt_val_x, amt_top_y - line_h - 8)

        # Balance Amount (highlighted gold)
        draw_text(amt_label_x, amt_top_y - line_h * 2 - 10, "Balance Amount:", font='Helvetica-Bold', size=11, color=GOLD)
        draw_right_text(amt_val_x, amt_top_y - line_h * 2 - 10, f"Rs. {balance:,.2f}", font='Helvetica-Bold', size=11, color=GOLD)

        # ════════════════════════════════════════════════════════
        # SECTION 7 — FOOTER
        # ════════════════════════════════════════════════════════
        footer_h = 36
        draw_rect(0, 0, W, footer_h, fill_color=BLACK)
        draw_text(30, footer_h - 14, "R SUNDARAM & CO  \u2022  READYMIX CONCRETE",
                  font='Helvetica-Bold', size=8, color=GOLD)
        draw_text(30, footer_h - 26, "Strong Roads  \u2022  Build To Last",
                  font='Helvetica', size=7, color=WHITE)

        # Outer border
        c.setStrokeColor(GOLD)
        c.setLineWidth(1.5)
        c.rect(10, 10, W - 20, H - 20, fill=0, stroke=1)

        c.showPage()
        c.save()
        buffer.seek(0)

        response = make_response(buffer.getvalue())
        response.headers['Content-Disposition'] = f'inline; filename=delivery_challan_{billing_id}.pdf'
        response.headers['Content-Type'] = 'application/pdf'
        return response

    except Exception as e:
        logger.error(f"Error generating PDF: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return jsonify({"error": f"Error generating PDF: {str(e)}"}), 500

@app.route('/api/manual-billing/export', methods=['GET'])
def export_manual_billing_excel():
    if SUPABASE_CLIENT:
        try:
            response = SUPABASE_CLIENT.table("manual_billing").select("*").execute()
            billing_records = response.data if response.data else []
        except Exception as e:
            logger.error(f"Supabase billing export error: {e}")
            billing_records = MOCK_DATABASE.get("manual_billing", [])
    else:
        billing_records = MOCK_DATABASE.get("manual_billing", [])
    
    wb = Workbook()
    ws = wb.active
    ws.title = "Manual Billing"
    
    headers = ["ID", "Company Name", "Phone", "Address", "Date", "Time", "Vehicle Number", "Driver Name", "Grade", "Cubic Meters", "Rate per m³", "Total Amount", "Advance Given", "Balance Amount", "Loading Time", "Unloading Time", "Created At"]
    ws.append(headers)
    
    for col in range(1, len(headers) + 1):
        cell = ws.cell(row=1, column=col)
        cell.font = Font(bold=True, color="FFFFFF")
        cell.fill = PatternFill(start_color="4472C4", end_color="4472C4", fill_type="solid")
        cell.alignment = Alignment(horizontal="center")
    
    for record in billing_records:
        ws.append([
            record.get('id', ''),
            record.get('company_name', ''),
            record.get('phone', ''),
            record.get('address', ''),
            record.get('date', ''),
            record.get('time', ''),
            record.get('vehicle_number', ''),
            record.get('driver_name', ''),
            record.get('grade', ''),
            record.get('cubic_meters', 0),
            record.get('rate_per_cubic', 0),
            record.get('total_amount', 0),
            record.get('advance_amount', 0),
            record.get('balance_amount', 0),
            record.get('loading_time', ''),
            record.get('unloading_time', ''),
            record.get('created_at', '')
        ])
    
    from io import BytesIO
    output = BytesIO()
    wb.save(output)
    output.seek(0)
    
    response = make_response(output.getvalue())
    response.headers['Content-Disposition'] = 'attachment; filename=manual_billing_export.xlsx'
    response.headers['Content-Type'] = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    return response

# Expense Management Module
@app.route('/api/expenses', methods=['GET', 'POST'])
def expenses():
    if request.method == 'GET':
        if SUPABASE_CLIENT:
            try:
                response = SUPABASE_CLIENT.table("expenses").select("*").execute()
                expense_records = response.data if response.data else []
            except Exception as e:
                logger.error(f"Supabase expenses fetch error: {e}")
                expense_records = MOCK_DATABASE.get("expenses", [])
        else:
            expense_records = MOCK_DATABASE.get("expenses", [])
        return jsonify({"success": True, "data": expense_records})
    
    elif request.method == 'POST':
        data = request.json

        # Only category and date are always required
        if not data.get('category') or not data.get('date'):
            return jsonify({"error": "Category and Date are required"}), 400

        # Build the record — capture ALL fields the frontend may send
        expense_record = {
            "id": f"expense-{len(MOCK_DATABASE.get('expenses', [])) + 1}",
            "category":       data.get('category', ''),
            "date":           data.get('date', ''),
            "description":    data.get('description', ''),
            # Raw-material specific fields
            "material_type":  data.get('material_type', ''),
            "quantity":       data.get('quantity', ''),
            "rate_per_ton":   data.get('rate_per_ton', ''),
            # Financial fields
            "amount":         data.get('amount', 0),
            "total_amount":   data.get('total_amount', data.get('amount', 0)),
            "advance_amount": data.get('advance_amount', 0),
            "balance_amount": data.get('balance_amount', data.get('amount', 0)),
            "created_at":     datetime.now().isoformat(),
            "created_by":     session.get('username', 'system')
        }

        if SUPABASE_CLIENT:
            try:
                SUPABASE_CLIENT.table("expenses").insert(expense_record).execute()
            except Exception as e:
                logger.error(f"Supabase expense insert error: {e}")
        else:
            MOCK_DATABASE.setdefault("expenses", []).append(expense_record)
            save_db()  # Persist to disk

        return jsonify({"success": True, "data": expense_record})

@app.route('/api/expenses/<expense_id>', methods=['PUT', 'DELETE'])
def expense_detail(expense_id):
    if request.method == 'PUT':
        data = request.json
        
        if SUPABASE_CLIENT:
            try:
                SUPABASE_CLIENT.table("expenses").update(data).eq("id", expense_id).execute()
            except Exception as e:
                logger.error(f"Supabase expense update error: {e}")
        else:
            for record in MOCK_DATABASE.get("expenses", []):
                if record['id'] == expense_id:
                    record.update(data)
                    break
            save_db()  # Persist to disk
        
        return jsonify({"success": True})
    
    elif request.method == 'DELETE':
        if SUPABASE_CLIENT:
            try:
                SUPABASE_CLIENT.table("expenses").delete().eq("id", expense_id).execute()
            except Exception as e:
                logger.error(f"Supabase expense delete error: {e}")
        else:
            MOCK_DATABASE["expenses"] = [r for r in MOCK_DATABASE.get("expenses", []) if r['id'] != expense_id]
            save_db()  # Persist to disk
        
        return jsonify({"success": True})

# ── Per-expense PDF Invoice ──────────────────────────────────────────────────
@app.route('/api/expenses/<expense_id>/pdf', methods=['GET'])
def expense_pdf(expense_id):
    from io import BytesIO
    from reportlab.lib.pagesizes import A4
    from reportlab.lib import colors
    from reportlab.pdfgen import canvas as pdf_canvas
    import os

    try:
        rec = None
        if SUPABASE_CLIENT:
            try:
                resp = SUPABASE_CLIENT.table("expenses").select("*").eq("id", expense_id).execute()
                if resp.data:
                    rec = resp.data[0]
            except Exception as e:
                logger.error(f"Supabase expense fetch error: {e}")
        else:
            for r in MOCK_DATABASE.get("expenses", []):
                if r['id'] == expense_id:
                    rec = r
                    break

        if not rec:
            return jsonify({"error": "Expense record not found"}), 404

        buffer = BytesIO()
        W, H = A4
        c = pdf_canvas.Canvas(buffer, pagesize=A4)

        GOLD      = colors.HexColor('#D4AF37')
        DARK_GOLD = colors.HexColor('#B8962E')
        BLACK     = colors.HexColor('#1a1a1a')
        WHITE     = colors.white
        LIGHT_GRAY = colors.HexColor('#f5f5f5')
        MID_GRAY  = colors.HexColor('#e0e0e0')
        GREEN     = colors.HexColor('#22c55e')

        def dt(x, y, text, font='Helvetica', size=9, color=BLACK):
            c.setFont(font, size); c.setFillColor(color); c.drawString(x, y, str(text))

        def drt(x, y, text, font='Helvetica', size=9, color=BLACK):
            c.setFont(font, size); c.setFillColor(color); c.drawRightString(x, y, str(text))

        def drect(x, y, w, h, fill=None, stroke=None, sw=0.5):
            c.setLineWidth(sw)
            if fill: c.setFillColor(fill)
            if stroke: c.setStrokeColor(stroke)
            if fill and stroke: c.rect(x, y, w, h, fill=1, stroke=1)
            elif fill: c.rect(x, y, w, h, fill=1, stroke=0)
            elif stroke: c.rect(x, y, w, h, fill=0, stroke=1)

        # ── HEADER BANNER ─────────────────────────────────────────
        banner_h = 100; banner_y = H - banner_h
        drect(0, banner_y, W, banner_h, fill=GOLD)

        logo_box_w, logo_box_h = 90, 76
        logo_box_x = 18; logo_box_y = banner_y + (banner_h - logo_box_h) / 2
        drect(logo_box_x, logo_box_y, logo_box_w, logo_box_h, fill=BLACK)

        logo_path = os.path.join('static', 'images', 'logo.png')
        if os.path.exists(logo_path):
            try:
                c.drawImage(logo_path, logo_box_x+5, logo_box_y+5,
                            width=logo_box_w-10, height=logo_box_h-10,
                            preserveAspectRatio=True, mask='auto')
            except Exception as e:
                logger.error(f"Logo draw error: {e}")

        cx = logo_box_x + logo_box_w + 16
        cy = banner_y + banner_h / 2
        dt(cx, cy+18, "R SUNDARAM & CO",         font='Helvetica-Bold', size=16, color=BLACK)
        dt(cx, cy+4,  "STRONG ROADS  BUILD TO LAST", font='Helvetica', size=8,  color=BLACK)
        dt(cx, cy-10, "READYMIX CONCRETE",        font='Helvetica', size=8,  color=BLACK)

        px = W - 170; py = banner_y + 72
        dt(px, py,    "Proprietor",              font='Helvetica',      size=8,  color=BLACK)
        dt(px, py-14, "S MAGHESH",               font='Helvetica-Bold', size=12, color=BLACK)
        dt(px, py-27, "\u25a0 9940270304",          font='Helvetica',      size=8,  color=BLACK)
        dt(px, py-38, "\u25a0 rsundaram&co@gmail.com", font='Helvetica',  size=8,  color=BLACK)
        dt(px, py-49, "\u25a0 Quarry Rd, Tiruneermalai", font='Helvetica', size=8, color=BLACK)
        dt(px, py-60, "Chennai, Tamil Nadu 600132", font='Helvetica',    size=8,  color=BLACK)

        # Separator
        c.setStrokeColor(DARK_GOLD); c.setLineWidth(2); c.line(0, banner_y-3, W, banner_y-3)

        # ── TITLE ─────────────────────────────────────────────────
        title_y = banner_y - 44
        c.setFont('Helvetica-Bold', 20); c.setFillColor(GOLD)
        title = "EXPENSE INVOICE"
        tw = c.stringWidth(title, 'Helvetica-Bold', 20)
        c.drawString((W-tw)/2, title_y, title)
        c.setStrokeColor(GOLD); c.setLineWidth(1.5)
        c.line((W-tw)/2, title_y-4, (W-tw)/2+tw, title_y-4)

        # ── META ROW ─────────────────────────────────────────────
        meta_y = title_y - 28
        dt(30,     meta_y, "Expense ID:", font='Helvetica-Bold', size=9, color=BLACK)
        dt(100,    meta_y, str(rec.get('id','')), size=9)
        dt(W/2+10, meta_y, "Date:", font='Helvetica-Bold', size=9, color=BLACK)
        dt(W/2+50, meta_y, str(rec.get('date','')), size=9)

        # ── CATEGORY BADGE ───────────────────────────────────────
        cat_y = meta_y - 26
        cat = rec.get('category','')
        dt(30, cat_y, "Category:", font='Helvetica-Bold', size=9, color=BLACK)
        badge_x = 95; badge_w = c.stringWidth(cat,'Helvetica-Bold',9)+16
        drect(badge_x, cat_y-3, badge_w, 16, fill=GOLD)
        dt(badge_x+8, cat_y+1, cat, font='Helvetica-Bold', size=9, color=BLACK)

        # description
        if rec.get('description'):
            dt(30, cat_y-18, "Notes:", font='Helvetica-Bold', size=9, color=BLACK)
            dt(70, cat_y-18, str(rec.get('description','')), size=9)

        # ── DETAILS TABLE ────────────────────────────────────────
        is_raw = cat == 'Raw Material'
        tbl_top = cat_y - (50 if rec.get('description') else 36)
        tbl_left = 30; tbl_w = W - 60
        col1 = tbl_w * 0.45; row_h = 28; hdr_h = 28

        drect(tbl_left, tbl_top-hdr_h, tbl_w, hdr_h, fill=GOLD)
        dt(tbl_left+10, tbl_top-hdr_h+9, "Field",   font='Helvetica-Bold', size=9, color=BLACK)
        dt(tbl_left+col1+10, tbl_top-hdr_h+9, "Value", font='Helvetica-Bold', size=9, color=BLACK)

        rows_data = []
        if is_raw:
            rows_data = [
                ("Material Type",    str(rec.get('material_type','—'))),
                ("Quantity",         f"{rec.get('quantity','—')} Tons"),
                ("Rate per Ton",     f"\u20b9 {float(rec.get('rate_per_ton',0)):,.2f}"),
            ]
        rows_data.append(("Total Amount", f"\u20b9 {float(rec.get('total_amount', rec.get('amount',0))):,.2f}"))
        if is_raw:
            rows_data.append(("Advance Given",  f"\u20b9 {float(rec.get('advance_amount',0)):,.2f}"))
            rows_data.append(("Balance Due",    f"\u20b9 {float(rec.get('balance_amount',0)):,.2f}"))

        row_y = tbl_top - hdr_h
        for i, (field, val) in enumerate(rows_data):
            bg = LIGHT_GRAY if i%2==0 else WHITE
            drect(tbl_left, row_y-row_h, tbl_w, row_h, fill=bg, stroke=MID_GRAY, sw=0.4)
            c.setStrokeColor(MID_GRAY); c.setLineWidth(0.4)
            c.line(tbl_left+col1, row_y-row_h, tbl_left+col1, row_y)
            is_last = (i == len(rows_data)-1)
            val_color = GREEN if (is_raw and is_last) else BLACK
            dt(tbl_left+10, row_y-row_h+9, field, font='Helvetica', size=9, color=BLACK)
            dt(tbl_left+col1+10, row_y-row_h+9, val, font='Helvetica-Bold', size=9, color=val_color)
            row_y -= row_h

        # ── FOOTER ───────────────────────────────────────────────
        drect(0, 0, W, 36, fill=BLACK)
        dt(30, 22, "R SUNDARAM & CO  \u2022  READYMIX CONCRETE", font='Helvetica-Bold', size=8, color=GOLD)
        dt(30, 10, "Strong Roads  \u2022  Build To Last", font='Helvetica', size=7, color=WHITE)

        c.setStrokeColor(GOLD); c.setLineWidth(1.5)
        c.rect(10, 10, W-20, H-20, fill=0, stroke=1)

        c.showPage(); c.save(); buffer.seek(0)

        resp = make_response(buffer.getvalue())
        resp.headers['Content-Disposition'] = f'inline; filename=expense_{expense_id}.pdf'
        resp.headers['Content-Type'] = 'application/pdf'
        return resp

    except Exception as e:
        logger.error(f"Expense PDF error: {e}")
        import traceback; logger.error(traceback.format_exc())
        return jsonify({"error": str(e)}), 500


# ── Per-expense Excel ────────────────────────────────────────────────────────
@app.route('/api/expenses/<expense_id>/excel', methods=['GET'])
def expense_excel(expense_id):
    try:
        rec = None
        if SUPABASE_CLIENT:
            try:
                resp = SUPABASE_CLIENT.table("expenses").select("*").eq("id", expense_id).execute()
                if resp.data:
                    rec = resp.data[0]
            except Exception as e:
                logger.error(f"Supabase expense fetch error: {e}")
        else:
            for r in MOCK_DATABASE.get("expenses", []):
                if r['id'] == expense_id:
                    rec = r
                    break

        if not rec:
            return jsonify({"error": "Expense record not found"}), 404

        wb = Workbook()
        ws = wb.active
        ws.title = "Expense Invoice"

        gold_fill   = PatternFill(start_color="D4AF37", end_color="D4AF37", fill_type="solid")
        black_fill  = PatternFill(start_color="1A1A1A", end_color="1A1A1A", fill_type="solid")
        header_font = Font(bold=True, color="1A1A1A", size=11)
        white_font  = Font(bold=True, color="FFFFFF", size=11)
        gold_font   = Font(bold=True, color="D4AF37", size=11)
        center      = Alignment(horizontal="center", vertical="center")
        left        = Alignment(horizontal="left", vertical="center")

        # Title rows
        ws.merge_cells('A1:H1')
        ws['A1'] = "R SUNDARAM & CO — EXPENSE INVOICE"
        ws['A1'].font = Font(bold=True, color="D4AF37", size=14)
        ws['A1'].fill = black_fill
        ws['A1'].alignment = center

        ws.merge_cells('A2:H2')
        ws['A2'] = "Strong Roads  •  Build To Last"
        ws['A2'].font = Font(color="888888", size=9)
        ws['A2'].fill = black_fill
        ws['A2'].alignment = center

        ws.append([])  # blank row

        # Column headers
        headers = ["Expense ID","Date","Category","Material Type","Qty (Tons)","Rate/Ton (₹)","Total (₹)","Advance (₹)","Balance (₹)","Description","Created At"]
        ws.append(headers)
        for col_idx, _ in enumerate(headers, 1):
            cell = ws.cell(row=4, column=col_idx)
            cell.fill = gold_fill
            cell.font = header_font
            cell.alignment = center

        # Data row
        ws.append([
            rec.get('id',''),
            rec.get('date',''),
            rec.get('category',''),
            rec.get('material_type','—'),
            rec.get('quantity','—'),
            rec.get('rate_per_ton','—'),
            float(rec.get('total_amount', rec.get('amount', 0))),
            float(rec.get('advance_amount', 0)),
            float(rec.get('balance_amount', 0)),
            rec.get('description',''),
            rec.get('created_at',''),
        ])
        for col_idx in range(1, 12):
            ws.cell(row=5, column=col_idx).alignment = left

        # Column widths
        for col, width in zip(['A','B','C','D','E','F','G','H','I','J','K'], [20,14,16,16,12,14,14,14,14,28,22]):
            ws.column_dimensions[col].width = width
        ws.row_dimensions[1].height = 26
        ws.row_dimensions[2].height = 16
        ws.row_dimensions[4].height = 20

        from io import BytesIO
        buf = BytesIO()
        wb.save(buf); buf.seek(0)

        resp = make_response(buf.getvalue())
        resp.headers['Content-Disposition'] = f'attachment; filename=expense_{expense_id}.xlsx'
        resp.headers['Content-Type'] = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        return resp

    except Exception as e:
        logger.error(f"Expense Excel error: {e}")
        return jsonify({"error": str(e)}), 500



@app.route('/api/expenses/export', methods=['GET'])
def export_expenses_excel():
    if SUPABASE_CLIENT:
        try:
            response = SUPABASE_CLIENT.table("expenses").select("*").execute()
            expense_records = response.data if response.data else []
        except Exception as e:
            logger.error(f"Supabase expenses export error: {e}")
            expense_records = MOCK_DATABASE.get("expenses", [])
    else:
        expense_records = MOCK_DATABASE.get("expenses", [])
    
    wb = Workbook()
    ws = wb.active
    ws.title = "Expenses"
    
    headers = ["ID", "Category", "Amount", "Description", "Date", "Created At", "Created By"]
    ws.append(headers)
    
    for col in range(1, len(headers) + 1):
        cell = ws.cell(row=1, column=col)
        cell.font = Font(bold=True, color="FFFFFF")
        cell.fill = PatternFill(start_color="4472C4", end_color="4472C4", fill_type="solid")
        cell.alignment = Alignment(horizontal="center")
    
    for record in expense_records:
        ws.append([
            record.get('id', ''),
            record.get('category', ''),
            record.get('amount', 0),
            record.get('description', ''),
            record.get('date', ''),
            record.get('created_at', ''),
            record.get('created_by', '')
        ])
    
    from io import BytesIO
    output = BytesIO()
    wb.save(output)
    output.seek(0)
    
    response = make_response(output.getvalue())
    response.headers['Content-Disposition'] = 'attachment; filename=expenses_export.xlsx'
    response.headers['Content-Type'] = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    return response

@app.route('/api/rmc/export/payments', methods=['GET'])
def export_payments_excel():
    client_id = request.args.get('client_id')
    
    if SUPABASE_CLIENT:
        try:
            query = SUPABASE_CLIENT.table("rmc_payment_records").select("*")
            if client_id:
                query = query.eq("client_id", client_id)
            response = query.execute()
            payments = response.data if response.data else []
        except Exception as e:
            logger.error(f"Supabase export error: {e}")
            payments = MOCK_DATABASE["rmc_payments"]
    else:
        payments = MOCK_DATABASE["rmc_payments"]
        if client_id:
            payments = [p for p in payments if p.get('client_id') == client_id]
    
    wb = Workbook()
    ws = wb.active
    ws.title = "Payments"
    
    headers = ["Payment Number", "Invoice ID", "Client ID", "Payment Date", "Amount", "Method", "Reference", "Notes"]
    ws.append(headers)
    
    for col in range(1, len(headers) + 1):
        cell = ws.cell(row=1, column=col)
        cell.font = Font(bold=True, color="FFFFFF")
        cell.fill = PatternFill(start_color="4472C4", end_color="4472C4", fill_type="solid")
        cell.alignment = Alignment(horizontal="center")
    
    for payment in payments:
        ws.append([
            payment.get('payment_number', ''),
            payment.get('invoice_id', ''),
            payment.get('client_id', ''),
            payment.get('payment_date', ''),
            payment.get('amount', 0),
            payment.get('payment_method', ''),
            payment.get('reference_number', ''),
            payment.get('notes', '')
        ])
    
    from io import BytesIO
    output = BytesIO()
    wb.save(output)
    output.seek(0)
    
    response = make_response(output.getvalue())
    response.headers['Content-Disposition'] = 'attachment; filename=rmc_payments_export.xlsx'
    response.headers['Content-Type'] = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    return response

@app.route('/api/rmc/payment/<payment_id>/receipt', methods=['GET'])
def generate_payment_receipt(payment_id):
    from io import BytesIO
    
    # Get payment data
    payment = None
    if SUPABASE_CLIENT:
        try:
            response = SUPABASE_CLIENT.table("rmc_payment_records").select("*").eq("id", payment_id).execute()
            if response.data:
                payment = response.data[0]
        except Exception as e:
            logger.error(f"Supabase payment query error: {e}")
    
    if not payment:
        payment = next((p for p in MOCK_DATABASE["rmc_payments"] if p['id'] == payment_id), None)
    
    if not payment:
        return jsonify({"error": "Payment not found"}), 404
    
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    elements = []
    styles = getSampleStyleSheet()
    
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=colors.HexColor('#1a1a1a'),
        spaceAfter=30
    )
    elements.append(Paragraph("PAYMENT RECEIPT", title_style))
    elements.append(Spacer(1, 20))
    
    receipt_data = [
        ["Payment Number:", payment.get('payment_number', '')],
        ["Payment Date:", payment.get('payment_date', '')],
        ["Amount:", f"₹{payment.get('amount', 0):,.2f}"],
        ["Payment Method:", payment.get('payment_method', '')],
        ["Reference:", payment.get('reference_number', 'N/A')]
    ]
    
    receipt_table = Table(receipt_data, colWidths=[150, 300])
    receipt_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    elements.append(receipt_table)
    
    doc.build(elements)
    buffer.seek(0)
    
    response = make_response(buffer.getvalue())
    response.headers['Content-Disposition'] = f'attachment; filename=receipt_{payment.get("payment_number", "")}.pdf'
    response.headers['Content-Type'] = 'application/pdf'
    return response

# ── Combined Report PDF ──────────────────────────────────────────────────────
@app.route('/api/reports/combined/pdf', methods=['GET'])
def combined_report_pdf():
    from io import BytesIO
    from reportlab.lib.pagesizes import A4
    from reportlab.lib import colors
    from reportlab.pdfgen import canvas as pdf_canvas
    from datetime import datetime as dt2
    import os

    report_type = request.args.get('type', 'combined')
    start_date  = request.args.get('start', '')
    end_date    = request.args.get('end', '')

    try:
        # ── Fetch data ────────────────────────────────────────────
        if SUPABASE_CLIENT:
            try:
                bills = SUPABASE_CLIENT.table("manual_billing").select("*").execute().data or []
                exps  = SUPABASE_CLIENT.table("expenses").select("*").execute().data or []
            except Exception as e:
                logger.error(f"Supabase fetch error: {e}")
                bills = MOCK_DATABASE.get("manual_billing", [])
                exps  = MOCK_DATABASE.get("expenses", [])
        else:
            bills = MOCK_DATABASE.get("manual_billing", [])
            exps  = MOCK_DATABASE.get("expenses", [])

        # ── Apply date filter ─────────────────────────────────────
        if start_date and end_date:
            bills = [r for r in bills if start_date <= str(r.get('date','')) <= end_date]
            exps  = [r for r in exps  if start_date <= str(r.get('date','')) <= end_date]

        if report_type == 'billing':
            exps = []
        elif report_type == 'expenses':
            bills = []

        # ── Totals ────────────────────────────────────────────────
        billing_total  = sum(float(r.get('total_amount', 0)) for r in bills)
        expense_total  = sum(float(r.get('total_amount', r.get('amount', 0))) for r in exps)
        raw_mat_total  = sum(float(r.get('total_amount', 0)) for r in exps if r.get('category') == 'Raw Material')
        grand_total    = billing_total + expense_total
        date_range     = f"{start_date} to {end_date}" if start_date and end_date else "All Records"

        # ── Canvas helpers ────────────────────────────────────────
        buffer = BytesIO()
        W, H = A4
        c = pdf_canvas.Canvas(buffer, pagesize=A4)

        GOLD       = colors.HexColor('#D4AF37')
        DARK_GOLD  = colors.HexColor('#B8962E')
        BLACK      = colors.HexColor('#1a1a1a')
        WHITE      = colors.white
        LIGHT_GRAY = colors.HexColor('#f5f5f5')
        MID_GRAY   = colors.HexColor('#e0e0e0')
        GREEN      = colors.HexColor('#22c55e')
        RED        = colors.HexColor('#f87171')

        logo_path = os.path.join('static', 'images', 'logo.png')

        def draw_header(page_title="COMBINED REPORT"):
            banner_h = 90; banner_y = H - banner_h
            c.setFillColor(GOLD); c.rect(0, banner_y, W, banner_h, fill=1, stroke=0)
            # Logo box
            lbw, lbh = 80, 66; lbx = 16; lby = banner_y + (banner_h - lbh) / 2
            c.setFillColor(BLACK); c.rect(lbx, lby, lbw, lbh, fill=1, stroke=0)
            if os.path.exists(logo_path):
                try: c.drawImage(logo_path, lbx+4, lby+4, width=lbw-8, height=lbh-8, preserveAspectRatio=True, mask='auto')
                except: pass
            # Company name
            cx2 = lbx + lbw + 14; cy2 = banner_y + banner_h / 2
            c.setFont('Helvetica-Bold', 14); c.setFillColor(BLACK); c.drawString(cx2, cy2+14, "R SUNDARAM & CO")
            c.setFont('Helvetica', 8); c.drawString(cx2, cy2+2, "STRONG ROADS  BUILD TO LAST")
            c.setFont('Helvetica', 8); c.drawString(cx2, cy2-10, "READYMIX CONCRETE")
            # Proprietor
            px2 = W - 160; py2 = banner_y + 66
            c.setFont('Helvetica', 8); c.drawString(px2, py2, "Proprietor")
            c.setFont('Helvetica-Bold', 11); c.drawString(px2, py2-13, "S MAGHESH")
            c.setFont('Helvetica', 7.5)
            c.drawString(px2, py2-25, "\u25a0 9940270304")
            c.drawString(px2, py2-35, "\u25a0 rsundaram&co@gmail.com")
            c.drawString(px2, py2-45, "\u25a0 Quarry Rd, Tiruneermalai, Chennai")
            # Separator
            c.setStrokeColor(DARK_GOLD); c.setLineWidth(2); c.line(0, banner_y-3, W, banner_y-3)
            # Page title
            title_y = banner_y - 38
            c.setFont('Helvetica-Bold', 18); c.setFillColor(GOLD)
            tw = c.stringWidth(page_title, 'Helvetica-Bold', 18)
            c.drawString((W - tw) / 2, title_y, page_title)
            c.setStrokeColor(GOLD); c.setLineWidth(1.5)
            c.line((W-tw)/2, title_y-4, (W-tw)/2+tw, title_y-4)
            return title_y - 28  # return y cursor after title

        def draw_footer(page_num):
            c.setFillColor(BLACK); c.rect(0, 0, W, 30, fill=1, stroke=0)
            c.setFont('Helvetica-Bold', 7.5); c.setFillColor(GOLD)
            c.drawString(30, 18, "R SUNDARAM & CO  \u2022  READYMIX CONCRETE  \u2022  Strong Roads  \u2022  Build To Last")
            c.setFont('Helvetica', 7); c.setFillColor(colors.HexColor('#888888'))
            c.drawRightString(W-30, 18, f"Page {page_num}")
            c.setStrokeColor(GOLD); c.setLineWidth(1.5)
            c.rect(10, 10, W-20, H-20, fill=0, stroke=1)

        def stat_box(x, y, w, h, label, value, val_color=GOLD):
            c.setFillColor(colors.HexColor('#222222')); c.setStrokeColor(GOLD); c.setLineWidth(0.8)
            c.roundRect(x, y, w, h, 6, fill=1, stroke=1)
            c.setFont('Helvetica', 8); c.setFillColor(colors.HexColor('#888888'))
            c.drawString(x+12, y+h-18, label)
            c.setFont('Helvetica-Bold', 13); c.setFillColor(val_color)
            c.drawString(x+12, y+10, str(value))

        # ════════════════════════════════════════════════════════
        # PAGE 1 — SUMMARY
        # ════════════════════════════════════════════════════════
        y = draw_header("COMBINED REPORT")
        page_num = 1

        # Meta strip
        c.setFont('Helvetica', 8.5); c.setFillColor(colors.HexColor('#888888'))
        c.drawString(30, y, f"Period: {date_range}   |   Generated: {dt2.now().strftime('%d %b %Y  %H:%M')}")
        y -= 28

        # Stat cards row 1
        bw = (W - 60) / 4 - 8; bh = 60
        stat_box(30,          y-bh, bw, bh, "TOTAL BILLS",           str(len(bills)),            GOLD)
        stat_box(30+bw+8,     y-bh, bw, bh, "BILLING REVENUE",       f"\u20b9 {billing_total:,.2f}", GOLD)
        stat_box(30+2*(bw+8), y-bh, bw, bh, "TOTAL EXPENSES",        str(len(exps)),              GOLD)
        stat_box(30+3*(bw+8), y-bh, bw, bh, "EXPENSE AMOUNT",        f"\u20b9 {expense_total:,.2f}", GOLD)
        y -= bh + 14

        bw2 = (W - 60) / 3 - 8
        stat_box(30,           y-bh, bw2, bh, "RAW MATERIAL SPEND",  f"\u20b9 {raw_mat_total:,.2f}", GOLD)
        stat_box(30+bw2+8,     y-bh, bw2, bh, "OTHER EXPENSES",      f"\u20b9 {expense_total-raw_mat_total:,.2f}", GOLD)
        stat_box(30+2*(bw2+8), y-bh, bw2, bh, "GRAND TOTAL",         f"\u20b9 {grand_total:,.2f}", GREEN)
        y -= bh + 22

        # Expense category breakdown
        cat_totals = {}
        for r in exps:
            cat = r.get('category', 'Other')
            cat_totals[cat] = cat_totals.get(cat, 0) + float(r.get('total_amount', r.get('amount', 0)))

        if cat_totals:
            c.setFont('Helvetica-Bold', 10); c.setFillColor(GOLD)
            c.drawString(30, y, "Expense Breakdown by Category")
            c.setStrokeColor(GOLD); c.setLineWidth(0.8)
            c.line(30, y-4, 250, y-4)
            y -= 18
            for cat, amt in sorted(cat_totals.items(), key=lambda x: -x[1]):
                pct = (amt / expense_total * 100) if expense_total else 0
                c.setFont('Helvetica', 9); c.setFillColor(BLACK)
                c.drawString(40, y, f"\u2022  {cat}")
                c.setFont('Helvetica-Bold', 9)
                c.drawString(180, y, f"\u20b9 {amt:,.2f}")
                c.setFont('Helvetica', 9); c.setFillColor(colors.HexColor('#888888'))
                c.drawString(280, y, f"({pct:.1f}%)")
                c.setFillColor(BLACK)
                y -= 16
            y -= 8

        draw_footer(page_num)

        # ── Shared table dimensions (used by both billing & expense pages) ──
        tbl_x = 25; row_h = 20; hdr_h = 22

        # ════════════════════════════════════════════════════════
        # PAGE 2 — BILLING RECORDS TABLE
        # ════════════════════════════════════════════════════════
        if bills:
            c.showPage(); page_num += 1
            y = draw_header("BILLING RECORDS")

            # Table header
            cols_b = [('Date', 60), ('Company', 115), ('Vehicle', 75), ('Grade', 40),
                      ('m\u00b3', 35), ('Total \u20b9', 70), ('Balance \u20b9', 70)]


            # Draw header
            c.setFillColor(GOLD); c.rect(tbl_x, y-hdr_h, W-50, hdr_h, fill=1, stroke=0)
            cx3 = tbl_x + 5
            for label, cw in cols_b:
                c.setFont('Helvetica-Bold', 8); c.setFillColor(BLACK)
                c.drawString(cx3, y-hdr_h+7, label)
                cx3 += cw
            y -= hdr_h

            for i, r in enumerate(bills):
                if y < 60:  # new page
                    draw_footer(page_num); c.showPage(); page_num += 1
                    y = draw_header("BILLING RECORDS (cont.)")

                bg = LIGHT_GRAY if i % 2 == 0 else WHITE
                c.setFillColor(bg); c.rect(tbl_x, y-row_h, W-50, row_h, fill=1, stroke=0)
                c.setStrokeColor(MID_GRAY); c.setLineWidth(0.3)
                c.rect(tbl_x, y-row_h, W-50, row_h, fill=0, stroke=1)

                vals = [
                    str(r.get('date', '')),
                    str(r.get('company_name', ''))[:18],
                    str(r.get('vehicle_number', '')),
                    str(r.get('grade', '')),
                    str(r.get('cubic_meters', '')),
                    f"\u20b9{float(r.get('total_amount',0)):,.0f}",
                    f"\u20b9{float(r.get('balance_amount',0)):,.0f}",
                ]
                cx3 = tbl_x + 5
                for j, (val, (_, cw)) in enumerate(zip(vals, cols_b)):
                    c.setFont('Helvetica', 7.5); c.setFillColor(BLACK)
                    c.drawString(cx3, y-row_h+6, val)
                    cx3 += cw
                y -= row_h

            draw_footer(page_num)

        # ════════════════════════════════════════════════════════
        # PAGE 3 — EXPENSE RECORDS TABLE
        # ════════════════════════════════════════════════════════
        if exps:
            c.showPage(); page_num += 1
            y = draw_header("EXPENSE RECORDS")

            cols_e = [('Date', 60), ('Category', 90), ('Material', 80),
                      ('Qty(T)', 45), ('Rate/T', 55), ('Total \u20b9', 70), ('Balance \u20b9', 65)]
            tbl_x = 25

            c.setFillColor(GOLD); c.rect(tbl_x, y-hdr_h, W-50, hdr_h, fill=1, stroke=0)
            cx3 = tbl_x + 5
            for label, cw in cols_e:
                c.setFont('Helvetica-Bold', 8); c.setFillColor(BLACK)
                c.drawString(cx3, y-hdr_h+7, label)
                cx3 += cw
            y -= hdr_h

            for i, r in enumerate(exps):
                if y < 60:
                    draw_footer(page_num); c.showPage(); page_num += 1
                    y = draw_header("EXPENSE RECORDS (cont.)")

                bg = LIGHT_GRAY if i % 2 == 0 else WHITE
                c.setFillColor(bg); c.rect(tbl_x, y-row_h, W-50, row_h, fill=1, stroke=0)
                c.setStrokeColor(MID_GRAY); c.setLineWidth(0.3)
                c.rect(tbl_x, y-row_h, W-50, row_h, fill=0, stroke=1)

                total   = float(r.get('total_amount', r.get('amount', 0)))
                balance = float(r.get('balance_amount', total))
                vals = [
                    str(r.get('date', '')),
                    str(r.get('category', ''))[:14],
                    str(r.get('material_type', '\u2014'))[:12],
                    str(r.get('quantity', '\u2014')),
                    f"\u20b9{float(r.get('rate_per_ton',0)):,.0f}" if r.get('rate_per_ton') else '\u2014',
                    f"\u20b9{total:,.0f}",
                    f"\u20b9{balance:,.0f}",
                ]
                cx3 = tbl_x + 5
                for val, (_, cw) in zip(vals, cols_e):
                    c.setFont('Helvetica', 7.5); c.setFillColor(BLACK)
                    c.drawString(cx3, y-row_h+6, val)
                    cx3 += cw
                y -= row_h

            draw_footer(page_num)

        c.save(); buffer.seek(0)

        resp = make_response(buffer.getvalue())
        resp.headers['Content-Disposition'] = f'inline; filename=combined_report_{dt2.now().strftime("%Y%m%d")}.pdf'
        resp.headers['Content-Type'] = 'application/pdf'
        return resp

    except Exception as e:
        logger.error(f"Combined report PDF error: {e}")
        import traceback; logger.error(traceback.format_exc())
        return jsonify({"error": str(e)}), 500


if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)

