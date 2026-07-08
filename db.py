import sqlite3
from contextlib import contextmanager
import hashlib

def init_db(db_path):
    with get_db(db_path) as conn:
        conn.executescript("""
        CREATE TABLE IF NOT EXISTS settings (key TEXT PRIMARY KEY, value TEXT);
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE, password_hash TEXT, role TEXT DEFAULT 'staff'
        );
        CREATE TABLE IF NOT EXISTS invoices (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            invoice_no TEXT UNIQUE, type TEXT,
            customer_name TEXT, mobile TEXT, vehicle_no TEXT, model TEXT,
            invoice_date TEXT, payment_mode TEXT,
            subtotal REAL DEFAULT 0, discount REAL DEFAULT 0,
            gst_pct REAL DEFAULT 18, gst_amt REAL DEFAULT 0,
            grand_total REAL DEFAULT 0, notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS invoice_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            invoice_no TEXT, item_type TEXT,
            description TEXT, part_no TEXT,
            quantity REAL DEFAULT 1, rate REAL DEFAULT 0, amount REAL DEFAULT 0
        );
        CREATE TABLE IF NOT EXISTS bike_sales (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            invoice_no TEXT UNIQUE, colour TEXT, engine_no TEXT, frame_no TEXT,
            rto_charge REAL DEFAULT 0, insurance REAL DEFAULT 0,
            accessories REAL DEFAULT 0, ex_showroom REAL DEFAULT 0,
            finance_bank TEXT, amount_received REAL DEFAULT 0,
            balance REAL DEFAULT 0, sales_exec TEXT,
            customer_address TEXT, customer_email TEXT, id_proof TEXT
        );
        CREATE TABLE IF NOT EXISTS service_jobs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            invoice_no TEXT UNIQUE, job_card_no TEXT,
            km_reading TEXT, advisor TEXT,
            labour_total REAL DEFAULT 0, parts_total REAL DEFAULT 0
        );
        CREATE TABLE IF NOT EXISTS customers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT, mobile TEXT UNIQUE, email TEXT, address TEXT,
            vehicle_no TEXT, vehicle_model TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS service_stock (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            part_no TEXT DEFAULT '',
            item_name TEXT NOT NULL,
            hsn_code TEXT DEFAULT '',
            category TEXT DEFAULT 'Spare Part',
            quantity REAL DEFAULT 0,
            unit TEXT DEFAULT 'Nos',
            purchase_price REAL DEFAULT 0,
            selling_price REAL DEFAULT 0,
            low_stock_alert INTEGER DEFAULT 5,
            added_date TEXT,
            last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS expenses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            expense_date TEXT, category TEXT, description TEXT,
            amount REAL DEFAULT 0, payment_mode TEXT DEFAULT 'Cash',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        INSERT OR IGNORE INTO settings VALUES ('shop_name','Sri Yamaha Motors');
        INSERT OR IGNORE INTO settings VALUES ('dealer_code','YMD-TN-0001');
        INSERT OR IGNORE INTO settings VALUES ('address','12, Anna Nagar, Madurai - 625020');
        INSERT OR IGNORE INTO settings VALUES ('phone1','0452-2345678');
        INSERT OR IGNORE INTO settings VALUES ('phone2','98765 43210');
        INSERT OR IGNORE INTO settings VALUES ('email','info@sriyamaha.com');
        INSERT OR IGNORE INTO settings VALUES ('gstin','33ABCDE1234F1Z5');
        INSERT OR IGNORE INTO settings VALUES ('state','33 - Tamil Nadu');
        INSERT OR IGNORE INTO settings VALUES ('bike_counter','1');
        INSERT OR IGNORE INTO settings VALUES ('acc_counter','1');
        INSERT OR IGNORE INTO settings VALUES ('svc_counter','1');
        """)
        ex = conn.execute("SELECT id FROM users WHERE username='admin'").fetchone()
        if not ex:
            conn.execute("INSERT INTO users(username,password_hash,role) VALUES(?,?,?)",
                         ("admin", hash_password("admin123"), "admin"))

@contextmanager
def get_db(db_path):
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        yield conn; conn.commit()
    except Exception:
        conn.rollback(); raise
    finally:
        conn.close()

def hash_password(pw):
    return hashlib.sha256(pw.encode()).hexdigest()

def verify_password(db_path, username, password):
    with get_db(db_path) as conn:
        row = conn.execute("SELECT password_hash,role FROM users WHERE username=?",
                           (username,)).fetchone()
    if row and row["password_hash"] == hash_password(password):
        return True, row["role"]
    return False, None

def get_setting(db_path, key, default=""):
    with get_db(db_path) as conn:
        row = conn.execute("SELECT value FROM settings WHERE key=?", (key,)).fetchone()
    return row["value"] if row else default

def set_setting(db_path, key, value):
    with get_db(db_path) as conn:
        conn.execute("INSERT OR REPLACE INTO settings VALUES(?,?)", (key, str(value)))

def next_invoice_no(db_path, type_key):
    prefix = {"bike":"BIKE","acc":"ACC","svc":"SVC"}[type_key]
    num = int(get_setting(db_path, f"{type_key}_counter", "1"))
    inv_no = f"{prefix}-{str(num).zfill(4)}"
    set_setting(db_path, f"{type_key}_counter", num+1)
    return inv_no

def fmt_currency(val):
    try: return f"\u20b9{float(val):,.2f}"
    except: return "\u20b90.00"

def upsert_customer(db_path, name, mobile, email="", address="", vehicle_no="", model=""):
    if not mobile: return
    with get_db(db_path) as conn:
        ex = conn.execute("SELECT id FROM customers WHERE mobile=?", (mobile,)).fetchone()
        if ex:
            conn.execute("UPDATE customers SET name=?,email=?,address=?,vehicle_no=?,vehicle_model=? WHERE mobile=?",
                         (name,email,address,vehicle_no,model,mobile))
        else:
            conn.execute("INSERT INTO customers(name,mobile,email,address,vehicle_no,vehicle_model) VALUES(?,?,?,?,?,?)",
                         (name,mobile,email,address,vehicle_no,model))
