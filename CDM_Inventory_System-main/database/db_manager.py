import os
import json
import csv # Required for downloading reports
import datetime
import mysql.connector

def connect_db():
    return mysql.connector.connect(
        host="192.168.100.232",
        user="root",
        password="1234",
        database="inventory_db"
    )

# Ensure we use the correct absolute path for the database file


def _ensure_admin_users_columns(cursor):
    columns = [row[1] for row in cursor.fetchall()]

    if 'email' not in columns:
        cursor.execute("ALTER TABLE admin_users ADD COLUMN email TEXT")
    if 'reset_code' not in columns:
        cursor.execute("ALTER TABLE admin_users ADD COLUMN reset_code TEXT")
    if 'reset_code_expiry' not in columns:
        cursor.execute("ALTER TABLE admin_users ADD COLUMN reset_code_expiry TIMESTAMP")
    if 'reset_code_sent_at' not in columns:
        cursor.execute("ALTER TABLE admin_users ADD COLUMN reset_code_sent_at TIMESTAMP")
        
def _ensure_requests_columns(cursor):
    """Checks if the requests table is missing the asset_ids column and adds it."""
    cursor.execute("PRAGMA table_info(requests)")
    columns = [row[1] for row in cursor.fetchall()]
    
    if 'asset_ids' not in columns:
        print("Updating requests table: Adding asset_ids column...")
        cursor.execute("ALTER TABLE requests ADD COLUMN asset_ids TEXT DEFAULT '[]'")


def initialize_db():
    conn = connect_db()
    cursor = conn.cursor()

    # ADMIN TABLE
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS admin_users (
        id INT AUTO_INCREMENT PRIMARY KEY,
        username VARCHAR(50) UNIQUE,
        password VARCHAR(50),
        role VARCHAR(20),
        security_answer VARCHAR(100),
        email VARCHAR(100),
        reset_code VARCHAR(100),
        reset_code_expiry DATETIME,
        reset_code_sent_at DATETIME
    )
    """)

    # INVENTORY TABLE
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS inventory (
        id INT AUTO_INCREMENT PRIMARY KEY,
        item_name VARCHAR(100),
        brand VARCHAR(100),
        quantity INT,
        status VARCHAR(50),
        category VARCHAR(50),
        image_path TEXT,
        property_id VARCHAR(50) DEFAULT 'N/A'
    )
    """)

    # REQUESTS TABLE
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS requests (
        id INT AUTO_INCREMENT PRIMARY KEY,
        student_name VARCHAR(100),
        items_json TEXT,
        purpose TEXT,
        status VARCHAR(50) DEFAULT 'PENDING',
        date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        asset_ids TEXT
    )
    """)

    # DEFAULT ADMIN
    cursor.execute("SELECT COUNT(*) FROM admin_users WHERE username = %s", ("admin",))
    if cursor.fetchone()[0] == 0:
        cursor.execute("""
        INSERT INTO admin_users (username, password, role, security_answer, email)
        VALUES (%s, %s, %s, %s, %s)
        """, ("admin", "cdm123", "Admin", "recovery", "admin@cdm.local"))

    conn.commit()
    conn.close()

def verify_admin(username, password):
    """Checks credentials and returns (Success, Role) for the login signal."""
    try:
        conn = connect_db()
        cursor = conn.cursor()
        cursor.execute("SELECT role FROM admin_users WHERE username=%s AND password=%s", (username, password))
        result = cursor.fetchone()
        conn.close()
        # Returns tuple (True, 'Admin') or (True, 'Staff') if found, else (False, None)
        return (True, result[0]) if result else (False, None)
    except Exception as e:
        print(f"Login Error: {e}")
        return False, None

# --- PASSWORD RECOVERY LOGIC ---

def verify_security_answer(username, answer):
    conn = connect_db(); cursor = conn.cursor()
    cursor.execute("SELECT id FROM admin_users WHERE username=%s AND security_answer=%s", (username, answer))
    res = cursor.fetchone(); conn.close()
    return res is not None

def get_user_by_email(email):
    conn = connect_db(); cursor = conn.cursor()
    cursor.execute("SELECT id, username FROM admin_users WHERE email = %s", (email,))
    user = cursor.fetchone(); conn.close()
    return user

def store_reset_code(email, code, expiry, sent_at):
    try:
        conn = connect_db(); cursor = conn.cursor()
        cursor.execute("UPDATE admin_users SET reset_code=%s, reset_code_expiry=%s, reset_code_sent_at=%s WHERE email=%s", 
                       (code, expiry, sent_at, email))
        conn.commit(); conn.close(); return True
    except Exception as e:
        print(f"Store reset code error: {e}")
        return False

def get_reset_code_info(email):
    conn = connect_db(); cursor = conn.cursor()
    cursor.execute("SELECT reset_code, reset_code_expiry, reset_code_sent_at FROM admin_users WHERE email=%s", (email,))
    row = cursor.fetchone(); conn.close()
    return row

def verify_reset_code(email, code):
    conn = connect_db(); cursor = conn.cursor()
    cursor.execute("SELECT reset_code, reset_code_expiry FROM admin_users WHERE email=%s", (email,))
    row = cursor.fetchone(); conn.close()
    if not row:
        return False
    stored_code, expiry = row
    if stored_code != code or not expiry:
        return False
    try:
        expiry_dt = datetime.datetime.fromisoformat(expiry)
    except Exception:
        return False
    return expiry_dt >= datetime.datetime.utcnow()

def reset_password_by_email(email, new_password):
    try:
        conn = connect_db(); cursor = conn.cursor()
        cursor.execute("UPDATE admin_users SET password=%s, reset_code=NULL, reset_code_expiry=NULL, reset_code_sent_at=NULL WHERE email=%s", 
                       (new_password, email))
        conn.commit(); conn.close(); return True
    except Exception as e:
        print(f"Reset password by email error: {e}")
        return False

def reset_password(username, new_password):
    try:
        conn = connect_db(); cursor = conn.cursor()
        cursor.execute("UPDATE admin_users SET password=%s WHERE username=%s", (new_password, username))
        conn.commit(); conn.close(); return True
    except Exception as e:
        print(f"Reset password error: {e}")
        return False

# --- DOWNLOAD / EXPORT LOGIC ---

def export_to_csv(data, filename, headers):
    try:
        with open(filename, mode='w', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            writer.writerow(headers)
            writer.writerows(data)
        return True
    except Exception as e:
        print(f"Export Error: {e}")
        return False

# --- USER MANAGEMENT ---

def add_user(u, p, r, email=""):
    """Adds a user and assigns them a role (Admin or Staff)."""
    try:
        conn = connect_db(); c = conn.cursor()
        c.execute("INSERT INTO admin_users (username, password, role, security_answer, email) VALUES (%s,%s,%s,%s,%s)", 
                  (u, p, r, 'recovery', email))
        conn.commit(); conn.close(); return True
    except Exception as e:
        print(f"Add user error: {e}")
        return False

def update_admin_credentials(new_username, new_password):
    try:
        conn = connect_db(); cursor = conn.cursor()
        cursor.execute("UPDATE admin_users SET username = %s, password = %s WHERE id = 1", 
                       (new_username, new_password))
        conn.commit(); conn.close(); return True
    except Exception as e:
        print(f"Error updating admin: {e}")
        return False

def get_all_users():
    conn = connect_db(); cursor = conn.cursor()
    cursor.execute("SELECT id, username, role FROM admin_users")
    users = cursor.fetchall(); conn.close()
    return users

def get_user_by_id(user_id):
    conn = connect_db(); cursor = conn.cursor()
    cursor.execute("SELECT id, username, password, role, email FROM admin_users WHERE id=%s", (user_id,))
    user = cursor.fetchone(); conn.close()
    return user

def update_staff_credentials(user_id, username, password, email):
    try:
        conn = connect_db(); cursor = conn.cursor()
        cursor.execute("UPDATE admin_users SET username=%s, password=%s, email=%s WHERE id=%s", 
                       (username, password, email, user_id))
        conn.commit(); conn.close(); return True
    except Exception as e:
        print(f"Error updating staff credentials: {e}")
        return False

def delete_user(user_id):
    conn = connect_db(); cursor = conn.cursor()
    cursor.execute("DELETE FROM admin_users WHERE id = %s", (user_id,))
    conn.commit(); conn.close()

# --- INVENTORY LOGIC ---

def get_all_items():
    conn = connect_db(); c = conn.cursor()
    c.execute("SELECT * FROM inventory"); items = c.fetchall(); conn.close()
    return items

def add_inventory_item(name, brand, qty, cat, img="", prop_id="N/A"):
    conn = connect_db(); c = conn.cursor()
    c.execute("""INSERT INTO inventory (item_name, brand, quantity, status, category, image_path, property_id) 
                 VALUES (%s,%s,%s,%s,%s,%s,%s)""", (name, brand, qty, 'Available', cat, img, prop_id))
    conn.commit(); conn.close()

def update_inventory_item(item_id, name, brand, qty, cat, img, prop_id="N/A"):
    conn = connect_db(); c = conn.cursor()
    c.execute("""UPDATE inventory SET item_name=%s, brand=%s, quantity=%s, category=%s, image_path=%s, property_id=%s 
                 WHERE id=%s""", (name, brand, qty, cat, img, prop_id, item_id))
    conn.commit(); conn.close()

def delete_inventory_item(item_id):
    conn = connect_db(); c = conn.cursor()
    c.execute("DELETE FROM inventory WHERE id = %s", (item_id,))
    conn.commit(); conn.close()

def deduct_stock(item_name, quantity, prop_id="N/A"):
    """Deducts stock. If Equipment/Sound, marks specific Property ID as Borrowed."""
    conn = connect_db(); cursor = conn.cursor()
    if prop_id != "N/A":
        cursor.execute("""UPDATE inventory SET quantity = 0, status = 'Borrowed' 
                          WHERE item_name = %s AND property_id = %s""", (item_name, prop_id))
    else:
        cursor.execute("UPDATE inventory SET quantity = quantity - %s WHERE item_name = %s", (quantity, item_name))
    conn.commit(); conn.close()

def return_item(item_name, quantity, prop_id="N/A"):
    """Restores stock. If Equipment/Sound, marks specific Property ID as Available."""
    conn = connect_db(); cursor = conn.cursor()
    if prop_id != "N/A":
        cursor.execute("""UPDATE inventory SET quantity = 1, status = 'Available' 
                          WHERE item_name = %s AND property_id = %s""", (item_name, prop_id))
    else:
        cursor.execute("UPDATE inventory SET quantity = quantity + %s WHERE item_name = %s", (quantity, item_name))
    conn.commit(); conn.close()

# --- KIOSK GROUPING LOGIC ---

def get_grouped_items():
    """Returns unique item types with their total available quantity for the Kiosk grid."""
    conn = connect_db(); cursor = conn.cursor()
    # Groups by Name and Brand so identical assets appear as one card
    cursor.execute("""
        SELECT MIN(id), item_name, brand, SUM(quantity), status, category, image_path 
        FROM inventory 
        WHERE quantity > 0 
        GROUP BY item_name, brand
    """)
    items = cursor.fetchall(); conn.close()
    return items

def get_available_asset_id(name, brand):
    """Finds the first available individual unit's Property ID (Sticker Number)."""
    conn = connect_db(); cursor = conn.cursor()
    cursor.execute("""
        SELECT property_id FROM inventory 
        WHERE item_name = %s AND brand = %s AND quantity > 0 
        LIMIT 1
    """, (name, brand))
    result = cursor.fetchone(); conn.close()
    return result[0] if result else "N/A"

# --- REQUEST LOGIC ---

def add_request(name, items_dict, purpose, asset_ids_json="[]"):
    conn = connect_db(); c = conn.cursor()
    # Updated to include 4 columns: name, items, purpose, AND asset_ids
    c.execute("INSERT INTO requests (student_name, items_json, purpose, asset_ids) VALUES (%s, %s, %s, %s)", 
              (name, json.dumps(items_dict), purpose, asset_ids_json))
    conn.commit(); conn.close()

def get_all_requests():
    conn = connect_db(); c = conn.cursor()
    c.execute("SELECT * FROM requests ORDER BY id DESC"); r = c.fetchall(); conn.close()
    return r

def update_request_status(req_id, status):
    conn = connect_db(); c = conn.cursor()
    c.execute("UPDATE requests SET status = %s WHERE id = %s", (status, req_id))
    conn.commit(); conn.close()
    
# This ensures that whenever db_manager is imported, 
# it checks if the database and tables exist.
initialize_db()
