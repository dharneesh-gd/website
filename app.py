from flask import Flask, request, jsonify, send_from_directory
import sqlite3
import os
import time
import random
from flask_cors import CORS
from datetime import datetime, timedelta

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Use different database filenames to avoid locks
USERS_DB = "users_new.db"
ORDERS_DB = "orders_new.db"
ADMIN_DB = "admin_new.db"
DESIGNS_DB = "designs_fresh.db"

# ==================== DATABASE INITIALIZATION ====================

def init_users_db():
    """Initialize users database with cart and wishlist tables"""
    max_retries = 3
    retry_delay = 1
    
    for attempt in range(max_retries):
        try:
            conn = sqlite3.connect(USERS_DB)
            cur = conn.cursor()
            
            # Users table
            cur.execute("""CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                fname TEXT,
                lname TEXT,
                email TEXT,
                username TEXT UNIQUE,
                password TEXT,
                address TEXT DEFAULT '',
                mobile TEXT DEFAULT '',
                district TEXT DEFAULT '',
                profile_pic TEXT DEFAULT '',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )""")
            
            # Cart table - UPDATED WITH CUSTOMIZATION FIELDS
            cur.execute("""CREATE TABLE IF NOT EXISTS user_cart (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT,
                design_name TEXT,
                price REAL,
                quantity INTEGER,
                image_url TEXT,
                placement_position TEXT DEFAULT '',
                design_side TEXT DEFAULT 'front',
                design_width INTEGER DEFAULT 0,
                design_height INTEGER DEFAULT 0,
                custom_requirements TEXT DEFAULT '',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (username) REFERENCES users (username)
            )""")
            
            # Wishlist table
            cur.execute("""CREATE TABLE IF NOT EXISTS user_wishlist (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT,
                design_name TEXT,
                price REAL,
                image_url TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (username) REFERENCES users (username)
            )""")
            
            conn.commit()
            conn.close()
            print("✅ Users database with cart/wishlist initialized successfully!")
            return True
            
        except sqlite3.OperationalError as e:
            print(f"⚠ Attempt {attempt + 1}/{max_retries}: Users database locked, retrying in {retry_delay} second(s)...")
            if attempt < max_retries - 1:
                time.sleep(retry_delay)
            else:
                print(f"💥 Failed to initialize users database after {max_retries} attempts: {e}")
                return False

def init_orders_db():
    """Initialize separate orders database"""
    max_retries = 3
    retry_delay = 1
    
    for attempt in range(max_retries):
        try:
            conn = sqlite3.connect(ORDERS_DB)
            cur = conn.cursor()
            
            # Orders table - UPDATED WITH CUSTOMIZATION FIELDS
            cur.execute("""CREATE TABLE IF NOT EXISTS orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT,
                design_name TEXT,
                price REAL,
                quantity INTEGER,
                image_url TEXT,
                placement_position TEXT DEFAULT '',
                design_side TEXT DEFAULT 'front',
                design_width INTEGER DEFAULT 0,
                design_height INTEGER DEFAULT 0,
                custom_requirements TEXT DEFAULT '',
                order_date TEXT,
                status TEXT DEFAULT 'Pending',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )""")
            
            conn.commit()
            conn.close()
            print("✅ Orders database initialized successfully!")
            return True
            
        except sqlite3.OperationalError as e:
            print(f"⚠ Attempt {attempt + 1}/{max_retries}: Orders database locked, retrying in {retry_delay} second(s)...")
            if attempt < max_retries - 1:
                time.sleep(retry_delay)
            else:
                print(f"💥 Failed to initialize orders database after {max_retries} attempts: {e}")
                return False

def init_admin_db():
    """Initialize admin database"""
    max_retries = 3
    retry_delay = 1
    
    for attempt in range(max_retries):
        try:
            conn = sqlite3.connect(ADMIN_DB)
            cur = conn.cursor()
            
            # Admin users table
            cur.execute("""CREATE TABLE IF NOT EXISTS admin_users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE,
                password TEXT,
                full_name TEXT,
                email TEXT,
                role TEXT DEFAULT 'admin',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )""")
            
            # Admin settings table
            cur.execute("""CREATE TABLE IF NOT EXISTS admin_settings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                setting_key TEXT UNIQUE,
                setting_value TEXT
            )""")
            
            # Create default admin user if not exists
            try:
                cur.execute("INSERT OR IGNORE INTO admin_users (username, password, full_name, email, role) VALUES (?, ?, ?, ?, ?)",
                           ("admin", "admin123", "Super Admin", "admin@finegraphics.com", "super_admin"))
                conn.commit()
                print("✅ Default admin user created")
            except Exception as e:
                print(f"⚠ Admin user setup: {e}")
            
            conn.commit()
            conn.close()
            print("✅ Admin database initialized successfully!")
            return True
            
        except sqlite3.OperationalError as e:
            print(f"⚠ Attempt {attempt + 1}/{max_retries}: Admin database locked, retrying in {retry_delay} second(s)...")
            if attempt < max_retries - 1:
                time.sleep(retry_delay)
            else:
                print(f"💥 Failed to initialize admin database after {max_retries} attempts: {e}")
                return False

def update_designs_schema():
    """Update designs table to include width and height columns"""
    try:
        conn = sqlite3.connect(DESIGNS_DB)
        cur = conn.cursor()
        
        # Check if width and height columns exist
        cur.execute("PRAGMA table_info(designs)")
        columns = [col[1] for col in cur.fetchall()]
        
        # Add width column if it doesn't exist
        if 'width' not in columns:
            cur.execute("ALTER TABLE designs ADD COLUMN width INTEGER DEFAULT 0")
            print("✅ Added width column to designs table")
        
        # Add height column if it doesn't exist
        if 'height' not in columns:
            cur.execute("ALTER TABLE designs ADD COLUMN height INTEGER DEFAULT 0")
            print("✅ Added height column to designs table")
        
        conn.commit()
        conn.close()
        return True
        
    except Exception as e:
        print(f"💥 Error updating designs schema: {str(e)}")
        return False

def init_designs_db():
    """Initialize designs database with preview images support - UPDATED WITH DIMENSIONS"""
    try:
        if os.path.exists(DESIGNS_DB):
            os.remove(DESIGNS_DB)
            print(f"🗑 Removed old designs database: {DESIGNS_DB}")
        
        conn = sqlite3.connect(DESIGNS_DB)
        cur = conn.cursor()
        
        # Main designs table with single primary image - UPDATED WITH DIMENSIONS
        cur.execute("""CREATE TABLE designs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            price REAL NOT NULL,
            width INTEGER DEFAULT 0,
            height INTEGER DEFAULT 0,
            tags TEXT,
            description TEXT,
            image_data TEXT,
            image_type TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )""")
        
        # Preview images table for multiple preview images
        cur.execute("""CREATE TABLE design_previews (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            design_id INTEGER,
            preview_data TEXT,
            preview_type TEXT,
            sort_order INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (design_id) REFERENCES designs (id) ON DELETE CASCADE
        )""")
        
        print("🔄 Adding sample designs WITH DIMENSIONS...")
        # Sample designs with dimensions (width, height, calculated price = width × height × 10)
        sample_designs = [
            ("Business Card Premium", 8, 5, "business,professional,card", "Professional business card design with modern layout"),
            ("Flyer Design", 21, 15, "marketing,flyer,promotional", "Eye-catching flyer design for promotions"),
            ("Logo Design", 10, 10, "branding,logo,custom", "Custom logo creation for your brand"),
            ("Brochure Design", 30, 21, "marketing,brochure,print", "Tri-fold brochure design"),
            ("Social Media Post", 12, 12, "social-media,digital,post", "Engaging social media graphics")
        ]

        for name, width, height, tags, description in sample_designs:
            try:
                # Calculate price automatically: width × height × 10
                price = width * height * 10
                placeholder_image = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg=="
                cur.execute("INSERT INTO designs (name, price, width, height, tags, description, image_data, image_type) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                           (name, price, width, height, tags, description, placeholder_image, "image/png"))
                design_id = cur.lastrowid
                print(f"✅ Added sample design: {name} - {width}cm × {height}cm = ₹{price}")
                
            except Exception as e:
                print(f"⚠ Failed to insert sample design {name}: {e}")     
        
        conn.commit()
        conn.close()
        print("✅ Designs database WITH DIMENSIONS initialized successfully!")
        return True
        
    except Exception as e:
        print(f"💥 Designs database error: {e}")
        return False

def init_databases():
    """Initialize all databases - FIXED VERSION"""
    print("🔄 Initializing databases with new filenames...")
    
    # Initialize each database with error handling
    databases = [
        ("Users", init_users_db),
        ("Orders", init_orders_db),
        ("Admin", init_admin_db),
        ("Designs", init_designs_db)
    ]
    
    all_success = True
    for db_name, init_func in databases:
        print(f"🔄 Initializing {db_name} database...")
        success = init_func()
        if success:
            print(f"✅ {db_name} database initialized successfully!")
        else:
            print(f"❌ Failed to initialize {db_name} database!")
            all_success = False
    
    if all_success:
        print("🎉 All databases initialization completed!")
    else:
        print("⚠ Some databases failed to initialize!")
    
    return all_success

# ==================== SERVE STATIC FILES ====================

@app.route('/')
def serve_index():
    return send_from_directory(BASE_DIR, 'index.html')

@app.route('/<path:filename>')
def serve_static(filename):
    if filename.endswith('.html') or '.' not in filename:
        try:
            return send_from_directory(BASE_DIR, filename)
        except:
            if '.' not in filename:
                return send_from_directory(BASE_DIR, filename + '.html')
            return "File not found", 404
    return send_from_directory(BASE_DIR, filename)

# ==================== USER ROUTES ====================

@app.route('/register', methods=['POST', 'GET'])
def register():
    if request.method == 'POST':
        try:
            data = request.get_json()
            if not data:
                return jsonify({"success": False, "message": "No data received"}), 400
                
            fname = data.get("fname")
            lname = data.get("lname")
            email = data.get("email")
            username = data.get("username")
            password = data.get("password")

            print(f"📝 REGISTRATION ATTEMPT: {username}")

            if not all([fname, lname, email, username, password]):
                return jsonify({"success": False, "message": "All fields are required"}), 400

            conn = sqlite3.connect(USERS_DB)
            cur = conn.cursor()
            
            try:
                cur.execute("INSERT INTO users (fname, lname, email, username, password) VALUES (?, ?, ?, ?, ?)",
                           (fname, lname, email, username, password))
                conn.commit()
                print(f"✅ USER REGISTERED: {username}")
                return jsonify({"success": True, "message": "Registration successful"})
            except sqlite3.IntegrityError:
                return jsonify({"success": False, "message": "Username already exists"}), 400
            except Exception as e:
                return jsonify({"success": False, "message": f"Database error: {str(e)}"}), 500
            finally:
                conn.close()
                
        except Exception as e:
            print(f"💥 REGISTRATION ERROR: {str(e)}")
            return jsonify({"success": False, "message": f"Server error: {str(e)}"}), 500
    else:
        return send_from_directory(BASE_DIR, 'register.html')

@app.route('/login', methods=['POST', 'GET'])
def login():
    if request.method == 'POST':
        try:
            data = request.get_json()
            if not data:
                return jsonify({"success": False, "message": "No data received"}), 400
                
            username = data.get("username")
            password = data.get("password")

            print(f"🔐 USER LOGIN ATTEMPT: {username}")

            conn = sqlite3.connect(USERS_DB)
            cur = conn.cursor()
            
            cur.execute("SELECT * FROM users WHERE username=? AND password=?", (username, password))
            user = cur.fetchone()
            conn.close()

            if user:
                print(f"✅ USER LOGIN SUCCESS: {username}")
                
                user_data = {
                    "id": user[0],
                    "fname": user[1],
                    "lname": user[2],
                    "email": user[3],
                    "username": user[4],
                    "address": user[6] if len(user) > 6 else "",
                    "mobile": user[7] if len(user) > 7 else "",
                    "district": user[8] if len(user) > 8 else "",
                    "profile_pic": user[9] if len(user) > 9 else "https://via.placeholder.com/80",
                    "is_admin": False
                }
                return jsonify({"success": True, "user": user_data})
            else:
                print(f"❌ USER LOGIN FAILED: {username}")
                return jsonify({"success": False, "message": "Invalid username or password"}), 401
                
        except Exception as e:
            print(f"💥 USER LOGIN ERROR: {str(e)}")
            return jsonify({"success": False, "message": f"Server error: {str(e)}"}), 500
    else:
        return send_from_directory(BASE_DIR, 'login.html')

@app.route('/admin/init-designs-db', methods=['POST'])
def init_designs_db_force():
    """Force initialize designs database"""
    try:
        success = init_designs_db()
        if success:
            return jsonify({"success": True, "message": "Designs database initialized successfully"})
        else:
            return jsonify({"success": False, "message": "Failed to initialize designs database"}), 500
    except Exception as e:
        print(f"💥 INIT DESIGNS DB ERROR: {str(e)}")
        return jsonify({"success": False, "message": str(e)}), 500
    
@app.route('/updateProfile', methods=['POST'])
def update_profile():
    try:
        data = request.get_json()
        print(f"📝 PROFILE UPDATE REQUEST: {data}")
        
        username = data.get("username")
        address = data.get("address", "")
        mobile = data.get("mobile", "")
        district = data.get("district", "")
        profile_pic = data.get("profilePic", "")  # This handles base64 data

        if not username:
            return jsonify({"error": "Username is required"}), 400

        conn = sqlite3.connect(USERS_DB)
        cur = conn.cursor()
        
        cur.execute("SELECT * FROM users WHERE username=?", (username,))
        user_exists = cur.fetchone()
        
        if not user_exists:
            conn.close()
            return jsonify({"error": "User not found"}), 404
        
        # Update user with profile picture
        cur.execute("""UPDATE users 
                      SET address=?, mobile=?, district=?, profile_pic=?
                      WHERE username=?""",
                    (address, mobile, district, profile_pic, username))
        conn.commit()
        
        # Get updated user data
        cur.execute("SELECT * FROM users WHERE username=?", (username,))
        user = cur.fetchone()
        conn.close()

        if user:
            user_data = {
                "id": user[0],
                "fname": user[1],
                "lname": user[2],
                "email": user[3],
                "username": user[4],
                "address": user[6] if len(user) > 6 else "",
                "mobile": user[7] if len(user) > 7 else "",
                "district": user[8] if len(user) > 8 else "",
                "profile_pic": user[9] if len(user) > 9 else "https://via.placeholder.com/80",
                "is_admin": False
            }
            print(f"✅ PROFILE UPDATED SUCCESSFULLY: {username}")
            return jsonify(user_data)
        else:
            return jsonify({"error": "Failed to update profile"}), 500
            
    except Exception as e:
        print(f"💥 PROFILE UPDATE ERROR: {str(e)}")
        return jsonify({"error": f"Server error: {str(e)}"}), 500

# ==================== CART & WISHLIST SYNC ROUTES ====================

@app.route('/debug/designs-tables')
def debug_designs_tables():
    """Check if designs tables exist"""
    try:
        conn = sqlite3.connect(DESIGNS_DB)
        cur = conn.cursor()
        
        # Check what tables exist
        cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cur.fetchall()
        
        # Check designs table structure
        designs_columns = []
        if any('designs' in table for table in tables):
            cur.execute("PRAGMA table_info(designs)")
            designs_columns = cur.fetchall()
        
        conn.close()
        
        return jsonify({
            "database_file": DESIGNS_DB,
            "tables": [table[0] for table in tables],
            "designs_columns": [col[1] for col in designs_columns]
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
@app.route('/syncUserData', methods=['POST'])
def sync_user_data():
    """Sync both cart and wishlist for a user - IMPROVED to handle empty arrays correctly"""
    try:
        data = request.get_json()
        username = data.get('username')
        cart_data = data.get('cart', None)  # Use None instead of empty list
        wishlist_data = data.get('wishlist', None)  # Use None instead of empty list
        
        print(f"🔄 SYNC USER DATA: {username} - Cart: {len(cart_data) if cart_data else 'None'}, Wishlist: {len(wishlist_data) if wishlist_data else 'None'}")
        
        if not username:
            return jsonify({"success": False, "message": "Username required"}), 400
        
        # Sync cart only if cart_data is provided (not None)
        if cart_data is not None:
            cart_result = sync_cart_to_db(username, cart_data)
        else:
            cart_result = "skipped"
            print("🔄 Cart sync skipped - no cart data provided")
        
        # Sync wishlist only if wishlist_data is provided (not None)
        if wishlist_data is not None:
            wishlist_result = sync_wishlist_to_db(username, wishlist_data)
        else:
            wishlist_result = "skipped"
            print("🔄 Wishlist sync skipped - no wishlist data provided")
        
        return jsonify({
            "success": True, 
            "message": "User data synced successfully",
            "cart_synced": cart_result,
            "wishlist_synced": wishlist_result
        })
        
    except Exception as e:
        print(f"💥 SYNC USER DATA ERROR: {str(e)}")
        return jsonify({"success": False, "message": str(e)}), 500

def get_existing_wishlist(username):
    """Get existing wishlist from database"""
    try:
        conn = sqlite3.connect(USERS_DB)
        cur = conn.cursor()
        cur.execute("SELECT * FROM user_wishlist WHERE username=?", (username,))
        wishlist_items = cur.fetchall()
        conn.close()
        
        wishlist_list = []
        for item in wishlist_items:
            wishlist_list.append({
                "name": item[2],
                "price": float(item[3]),
                "image": item[4]
            })
        
        return wishlist_list
    except Exception as e:
        print(f"💥 GET EXISTING WISHLIST ERROR: {str(e)}")
        return []
    
def sync_cart_to_db(username, cart_items):
    """Sync cart data to database WITH CUSTOMIZATION FIELDS"""
    try:
        conn = sqlite3.connect(USERS_DB)
        cur = conn.cursor()
        
        # Clear existing cart for this user
        cur.execute("DELETE FROM user_cart WHERE username=?", (username,))
        
        # Save new cart items WITH CUSTOMIZATION FIELDS
        saved_count = 0
        for item in cart_items:
            try:
                cur.execute("""INSERT INTO user_cart (username, design_name, price, quantity, image_url, 
                              placement_position, design_side, design_width, design_height, custom_requirements) 
                              VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                            (username, item.get('name'), float(item.get('price', 0)), 
                             int(item.get('quantity', 1)), item.get('image', ''),
                             item.get('placement_position', ''), 
                             item.get('design_side', 'front'),
                             int(item.get('design_width', 0)),
                             int(item.get('design_height', 0)),
                             item.get('custom_requirements', '')))
                saved_count += 1
            except Exception as e:
                print(f"⚠ Failed to save cart item {item}: {e}")
                continue
        
        conn.commit()
        conn.close()
        
        print(f"✅ CART SYNCED TO DB: {saved_count} items for {username}")
        return saved_count
        
    except Exception as e:
        print(f"💥 CART SYNC ERROR: {str(e)}")
        return 0

def sync_wishlist_to_db(username, wishlist_items):
    """Sync wishlist data to database"""
    try:
        conn = sqlite3.connect(USERS_DB)
        cur = conn.cursor()
        
        # Clear existing wishlist for this user
        cur.execute("DELETE FROM user_wishlist WHERE username=?", (username,))
        
        # Save new wishlist items
        saved_count = 0
        for item in wishlist_items:
            try:
                cur.execute("""INSERT INTO user_wishlist (username, design_name, price, image_url) 
                              VALUES (?, ?, ?, ?)""",
                            (username, item.get('name'), float(item.get('price', 0)), item.get('image', '')))
                saved_count += 1
            except Exception as e:
                print(f"⚠ Failed to save wishlist item {item}: {e}")
                continue
        
        conn.commit()
        conn.close()
        
        print(f"✅ WISHLIST SYNCED TO DB: {saved_count} items for {username}")
        return saved_count
        
    except Exception as e:
        print(f"💥 WISHLIST SYNC ERROR: {str(e)}")
        return 0

@app.route('/getUserData/<username>')
def get_user_data(username):
    """Get both cart and wishlist data for a user WITH CUSTOMIZATION FIELDS"""
    try:
        # Get cart data WITH CUSTOMIZATION FIELDS
        cart_conn = sqlite3.connect(USERS_DB)
        cart_cur = cart_conn.cursor()
        cart_cur.execute("SELECT * FROM user_cart WHERE username=?", (username,))
        cart_items = cart_cur.fetchall()
        cart_conn.close()
        
        cart_list = []
        for item in cart_items:
            cart_list.append({
                "name": item[2],
                "price": float(item[3]),
                "quantity": item[4],
                "image": item[5],
                "placement_position": item[6] if len(item) > 6 else '',
                "design_side": item[7] if len(item) > 7 else 'front',
                "design_width": item[8] if len(item) > 8 else 0,
                "design_height": item[9] if len(item) > 9 else 0,
                "custom_requirements": item[10] if len(item) > 10 else ''
            })
        
        # Get wishlist data
        wishlist_conn = sqlite3.connect(USERS_DB)
        wishlist_cur = wishlist_conn.cursor()
        wishlist_cur.execute("SELECT * FROM user_wishlist WHERE username=?", (username,))
        wishlist_items = wishlist_cur.fetchall()
        wishlist_conn.close()
        
        wishlist_list = []
        for item in wishlist_items:
            wishlist_list.append({
                "name": item[2],
                "price": float(item[3]),
                "image": item[4]
            })
        
        print(f"📦 USER DATA RETRIEVED: {username} - Cart: {len(cart_list)}, Wishlist: {len(wishlist_list)}")
        
        return jsonify({
            "success": True, 
            "cart": cart_list,
            "wishlist": wishlist_list
        })
        
    except Exception as e:
        print(f"💥 GET USER DATA ERROR: {str(e)}")
        return jsonify({"success": False, "message": str(e)}), 500

# ==================== CART ROUTES ====================

@app.route('/saveCart', methods=['POST'])
def save_cart():
    try:
        data = request.get_json()
        username = data.get('username')
        cart_items = data.get('cart', [])
        
        print(f"🛒 SAVE CART REQUEST: {username}, {len(cart_items)} items")
        
        if not username:
            return jsonify({"success": False, "message": "Username required"}), 400
        
        conn = sqlite3.connect(USERS_DB)
        cur = conn.cursor()
        
        # Clear existing cart for this user
        cur.execute("DELETE FROM user_cart WHERE username=?", (username,))
        
        # Save new cart items WITH CUSTOMIZATION FIELDS
        saved_count = 0
        for item in cart_items:
            try:
                cur.execute("""INSERT INTO user_cart (username, design_name, price, quantity, image_url,
                              placement_position, design_side, design_width, design_height, custom_requirements) 
                              VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                            (username, item.get('name'), float(item.get('price', 0)), 
                             int(item.get('quantity', 1)), item.get('image', ''),
                             item.get('placement_position', ''), 
                             item.get('design_side', 'front'),
                             int(item.get('design_width', 0)),
                             int(item.get('design_height', 0)),
                             item.get('custom_requirements', '')))
                saved_count += 1
            except Exception as e:
                print(f"⚠ Failed to save cart item {item}: {e}")
                continue
        
        conn.commit()
        conn.close()
        
        print(f"✅ CART SAVED: {saved_count} items for {username}")
        return jsonify({"success": True, "message": f"Cart saved with {saved_count} items"})
        
    except Exception as e:
        print(f"💥 SAVE CART ERROR: {str(e)}")
        return jsonify({"success": False, "message": str(e)}), 500

@app.route('/getCart/<username>')
def get_cart(username):
    try:
        conn = sqlite3.connect(USERS_DB)
        cur = conn.cursor()
        
        cur.execute("SELECT * FROM user_cart WHERE username=?", (username,))
        cart_items = cur.fetchall()
        conn.close()
        
        cart_list = []
        for item in cart_items:
            cart_list.append({
                "name": item[2],
                "price": float(item[3]),
                "quantity": item[4],
                "image": item[5],
                "placement_position": item[6] if len(item) > 6 else '',
                "design_side": item[7] if len(item) > 7 else 'front',
                "design_width": item[8] if len(item) > 8 else 0,
                "design_height": item[9] if len(item) > 9 else 0,
                "custom_requirements": item[10] if len(item) > 10 else ''
            })
        
        print(f"📦 CART RETRIEVED: {username} - {len(cart_list)} items")
        return jsonify({"success": True, "cart": cart_list})
        
    except Exception as e:
        print(f"💥 GET CART ERROR: {str(e)}")
        return jsonify({"success": False, "message": str(e)}), 500

@app.route('/clearCart/<username>', methods=['POST'])
def clear_cart(username):
    try:
        conn = sqlite3.connect(USERS_DB)
        cur = conn.cursor()
        
        cur.execute("DELETE FROM user_cart WHERE username=?", (username,))
        conn.commit()
        conn.close()
        
        print(f"✅ CART CLEARED: {username}")
        return jsonify({"success": True, "message": "Cart cleared"})
        
    except Exception as e:
        print(f"💥 CLEAR CART ERROR: {str(e)}")
        return jsonify({"success": False, "message": str(e)}), 500

# ==================== WISHLIST ROUTES ====================

@app.route('/saveWishlist', methods=['POST'])
def save_wishlist():
    try:
        data = request.get_json()
        username = data.get('username')
        wishlist_items = data.get('wishlist', [])
        
        print(f"❤ SAVE WISHLIST REQUEST: {username}, {len(wishlist_items)} items")
        
        if not username:
            return jsonify({"success": False, "message": "Username required"}), 400
        
        conn = sqlite3.connect(USERS_DB)
        cur = conn.cursor()
        
        # Clear existing wishlist for this user
        cur.execute("DELETE FROM user_wishlist WHERE username=?", (username,))
        
        # Save new wishlist items
        saved_count = 0
        for item in wishlist_items:
            try:
                cur.execute("""INSERT INTO user_wishlist (username, design_name, price, image_url) 
                              VALUES (?, ?, ?, ?)""",
                            (username, item.get('name'), float(item.get('price', 0)), item.get('image', '')))
                saved_count += 1
            except Exception as e:
                print(f"⚠ Failed to save wishlist item {item}: {e}")
                continue
        
        conn.commit()
        conn.close()
        
        print(f"✅ WISHLIST SAVED: {saved_count} items for {username}")
        return jsonify({"success": True, "message": f"Wishlist saved with {saved_count} items"})
        
    except Exception as e:
        print(f"💥 SAVE WISHLIST ERROR: {str(e)}")
        return jsonify({"success": False, "message": str(e)}), 500

@app.route('/getWishlist/<username>')
def get_wishlist(username):
    try:
        conn = sqlite3.connect(USERS_DB)
        cur = conn.cursor()
        
        cur.execute("SELECT * FROM user_wishlist WHERE username=?", (username,))
        wishlist_items = cur.fetchall()
        conn.close()
        
        wishlist_list = []
        for item in wishlist_items:
            wishlist_list.append({
                "name": item[2],
                "price": float(item[3]),
                "image": item[4]
            })
        
        print(f"❤ WISHLIST RETRIEVED: {username} - {len(wishlist_list)} items")
        return jsonify({"success": True, "wishlist": wishlist_list})
        
    except Exception as e:
        print(f"💥 GET WISHLIST ERROR: {str(e)}")
        return jsonify({"success": False, "message": str(e)}), 500

# ==================== ORDER ROUTES (orders.db) ====================

@app.route('/saveOrder', methods=['POST'])
def save_order():
    """Save order to database (self-contained with column check)"""
    try:
        print("📦 [saveOrder] Request received")

        data = request.get_json(force=True)
        print(f"🧾 Incoming data: {data}")

        if not data:
            return jsonify({"success": False, "message": "No data received"}), 400

        username = data.get("username")
        items = data.get("items", [])
        subtotal = float(data.get("subtotal", 0))
        tax = float(data.get("tax", 0))
        total = float(data.get("total", 0))

        if not username or not items:
            return jsonify({"success": False, "message": "Invalid order data"}), 400

        import random, time
        order_id = f"ORD{int(time.time())}{random.randint(1000, 9999)}"
        order_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # ✅ Connect to database
        conn = sqlite3.connect(ORDERS_DB)
        cur = conn.cursor()

        # ✅ Ensure the orders table exists
        cur.execute("""
            CREATE TABLE IF NOT EXISTS orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                order_id TEXT,
                username TEXT,
                design_name TEXT,
                price REAL,
                quantity INTEGER,
                image_url TEXT,
                placement_position TEXT DEFAULT '',
                design_side TEXT DEFAULT 'front',
                design_width INTEGER DEFAULT 0,
                design_height INTEGER DEFAULT 0,
                custom_requirements TEXT DEFAULT '',
                order_date TEXT,
                status TEXT DEFAULT 'Ordered',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # ✅ Check if subtotal/tax/total columns exist — add if missing
        cur.execute("PRAGMA table_info(orders)")
        columns = [col[1] for col in cur.fetchall()]

        if "subtotal" not in columns:
            cur.execute("ALTER TABLE orders ADD COLUMN subtotal REAL DEFAULT 0")
            print("🧩 Added missing 'subtotal' column")

        if "tax" not in columns:
            cur.execute("ALTER TABLE orders ADD COLUMN tax REAL DEFAULT 0")
            print("🧩 Added missing 'tax' column")

        if "total" not in columns:
            cur.execute("ALTER TABLE orders ADD COLUMN total REAL DEFAULT 0")
            print("🧩 Added missing 'total' column")

        # ✅ Insert order items safely
        for item in items:
            cur.execute("""
                INSERT INTO orders (
                    order_id, username, design_name, price, quantity, image_url,
                    placement_position, design_side, design_width, design_height,
                    custom_requirements, order_date, status, subtotal, tax, total
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                order_id,
                username,
                item.get("name", ""),
                float(item.get("price", 0)),
                int(item.get("quantity", 1)),
                item.get("image", ""),
                item.get("placement_position", ""),
                item.get("design_side", "front"),
                int(item.get("design_width", 0)),
                int(item.get("design_height", 0)),
                item.get("custom_requirements", ""),
                order_date,
                "Ordered",
                subtotal,
                tax,
                total
            ))

        conn.commit()
        conn.close()

        print(f"✅ Order saved successfully for {username} (Order ID: {order_id})")

        return jsonify({
            "success": True,
            "message": "Order saved successfully",
            "order_id": order_id
        })

    except Exception as e:
        print(f"💥 ERROR saving order: {e}")
        return jsonify({"success": False, "message": str(e)}), 500

@app.route('/getOrders/<username>')
def get_orders(username):
    """Get user orders from orders database - returns grouped orders with correct totals"""
    try:
        print(f"📦 GET ORDERS REQUEST FOR: {username}")

        conn = sqlite3.connect(ORDERS_DB)
        cur = conn.cursor()

        # Ensure table exists
        cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='orders'")
        if not cur.fetchone():
            conn.close()
            print("❌ Orders table not found")
            return jsonify({"success": True, "orders": []})

        # Fetch all rows for this user ordered by created_at (or order_date)
        cur.execute("PRAGMA table_info(orders)")
        cols_info = cur.fetchall()
        cols = [c[1] for c in cols_info]

        cur.execute("SELECT * FROM orders WHERE username=? ORDER BY order_date DESC, created_at DESC", (username,))
        rows = cur.fetchall()
        conn.close()

        # Map column name -> index
        col_index = {c[1]: i for i, c in enumerate(cols_info)}

        # Build grouped orders by order_id (fallback to generated group id)
        grouped = {}
        for row in rows:
            # get order_id if present, else use created_at+id fallback
            order_id = row[col_index['order_id']] if 'order_id' in col_index and row[col_index['order_id']] else f"ORD_ROW_{row[col_index['id']]}"

            if order_id not in grouped:
                grouped[order_id] = {
                    "order_id": order_id,
                    "date": row[col_index['order_date']] if 'order_date' in col_index else row[col_index['created_at']] if 'created_at' in col_index else "",
                    "status": row[col_index['status']] if 'status' in col_index else "Pending",
                    "items": [],
                    "subtotal": 0.0,
                    "tax": None,   # keep None to detect missing
                    "total": None
                }

            # read fields defensively
            price = None
            quantity = None
            try:
                price = float(row[col_index['price']]) if 'price' in col_index and row[col_index['price']] is not None else 0.0
            except:
                price = 0.0
            try:
                quantity = int(row[col_index['quantity']]) if 'quantity' in col_index and row[col_index['quantity']] is not None else 1
            except:
                quantity = 1

            item = {
                "name": row[col_index['design_name']] if 'design_name' in col_index else (row[col_index['id']] if 'id' in col_index else "Item"),
                "price": price,
                "quantity": quantity,
                "image": row[col_index['image_url']] if 'image_url' in col_index else "",
                "placement_position": row[col_index['placement_position']] if 'placement_position' in col_index else "",
                "design_side": row[col_index['design_side']] if 'design_side' in col_index else "front",
                "design_width": row[col_index['design_width']] if 'design_width' in col_index else 0,
                "design_height": row[col_index['design_height']] if 'design_height' in col_index else 0,
                "custom_requirements": row[col_index['custom_requirements']] if 'custom_requirements' in col_index else ""
            }

            grouped[order_id]['items'].append(item)
            grouped[order_id]['subtotal'] += (price * quantity)

            # if tax/total columns exist and have values, capture last non-null value
            if 'tax' in col_index and row[col_index['tax']] is not None:
                try:
                    grouped[order_id]['tax'] = float(row[col_index['tax']])
                except:
                    pass
            if 'total' in col_index and row[col_index['total']] is not None:
                try:
                    grouped[order_id]['total'] = float(row[col_index['total']])
                except:
                    pass

        # finalize computed totals (if tax/total were missing, compute)
        orders_out = []
        for oid, g in grouped.items():
            subtotal_val = round(float(g['subtotal'] or 0.0), 2)
            tax_val = g['tax'] if g['tax'] is not None else round(subtotal_val * 0.18, 2)
            total_val = g['total'] if g['total'] is not None else round(subtotal_val + tax_val, 2)

            orders_out.append({
                "order_id": g['order_id'],
                "date": g['date'],
                "status": g['status'],
                "items": g['items'],
                "subtotal": subtotal_val,
                "tax": tax_val,
                "total": total_val
            })

        # sort by date desc if date exists
        try:
            orders_out.sort(key=lambda x: x.get('date') or "", reverse=True)
        except:
            pass

        return jsonify({"success": True, "orders": orders_out})

    except Exception as e:
        print(f"💥 GET ORDERS ERROR: {e}")
        return jsonify({"success": False, "orders": [], "message": str(e)}), 500

# ==================== DESIGN ROUTES ====================

@app.route('/getDesigns')
def get_designs():
    """Get all designs for main website - UPDATED WITH DIMENSIONS"""
    try:
        conn = sqlite3.connect(DESIGNS_DB)
        cur = conn.cursor()
        
        cur.execute("SELECT id, name, price, width, height, tags, description, image_data, image_type FROM designs ORDER BY created_at DESC")
        designs = cur.fetchall()
        conn.close()
        
        design_list = []
        for design in designs:
            design_data = {
                "id": design[0],
                "name": design[1],
                "price": float(design[2]),
                "width": design[3] or 0,
                "height": design[4] or 0,
                "tags": design[5] or "",
                "description": design[6] or "",
                "image_data": design[7],
                "image_type": design[8]
            }
            design_list.append(design_data)
        
        print(f"🎨 Retrieved {len(design_list)} designs with dimensions for main website")
        return jsonify({"success": True, "designs": design_list})
    except Exception as e:
        print(f"💥 GET DESIGNS ERROR: {str(e)}")
        return jsonify({"success": False, "message": str(e)}), 500

@app.route('/admin/save-design', methods=['POST'])
def save_design():
    """Save or update a design in the designs database - UPDATED FOR AUTOMATIC PRICING"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"success": False, "message": "No data received"}), 400

        design_id = data.get("id")  # This will be None for new designs, present for edits
        name = data.get("name")
        width = data.get("width")  # NEW: Get width
        height = data.get("height")  # NEW: Get height
        description = data.get("description")
        tags = data.get("tags", "")
        images = data.get("images", [])
        delete_all_previews = data.get("delete_all_previews", False)

        # Validate required fields - REMOVED PRICE VALIDATION
        if not name or not width or not height or not description:
            return jsonify({"success": False, "message": "Missing required fields"}), 400

        # Validate dimensions
        try:
            width = int(width)
            height = int(height)
            if width <= 0 or height <= 0:
                return jsonify({"success": False, "message": "Dimensions must be greater than 0"}), 400
        except (ValueError, TypeError):
            return jsonify({"success": False, "message": "Invalid dimensions"}), 400

        # Calculate price automatically: width × height × 10
        price = width * height * 10

        # Take only first image (since you allow one)
        image_data = None
        image_type = None
        if images and len(images) > 0:
            image_data = images[0].get("image_data")
            image_type = images[0].get("image_type")

        conn = sqlite3.connect(DESIGNS_DB)
        cur = conn.cursor()
        
        if design_id:
            # UPDATE existing design
            if image_data and image_type:
                # Update with new image and dimensions
                cur.execute("""UPDATE designs SET name=?, price=?, width=?, height=?, tags=?, description=?, image_data=?, image_type=?
                               WHERE id=?""",
                            (name, price, width, height, tags, description, image_data, image_type, design_id))
            else:
                # Update without changing image, but with new dimensions
                cur.execute("""UPDATE designs SET name=?, price=?, width=?, height=?, tags=?, description=?
                               WHERE id=?""",
                            (name, price, width, height, tags, description, design_id))
            
            # Delete all preview images if requested
            if delete_all_previews:
                cur.execute("DELETE FROM design_previews WHERE design_id=?", (design_id,))
                print(f"🗑️ Deleted all preview images for design {design_id}")
            
            message = "Design updated successfully"
            print(f"✅ Design updated: {name} - {width}cm × {height}cm = ₹{price} (ID: {design_id})")
        else:
            # INSERT new design
            cur.execute("""INSERT INTO designs (name, price, width, height, tags, description, image_data, image_type)
                           VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                        (name, price, width, height, tags, description, image_data, image_type))
            design_id = cur.lastrowid
            message = "Design saved successfully"
            print(f"✅ New design saved: {name} - {width}cm × {height}cm = ₹{price} (ID: {design_id})")
        
        conn.commit()
        conn.close()

        return jsonify({"success": True, "message": message, "design_id": design_id, "calculated_price": price})
    except Exception as e:
        print(f"💥 SAVE DESIGN ERROR: {str(e)}")
        return jsonify({"success": False, "message": str(e)}), 500

@app.route('/admin/designs', methods=['GET'])
def get_all_designs():
    """Get all designs for admin - WITH DIMENSIONS AND PREVIEW COUNTS"""
    try:
        conn = sqlite3.connect(DESIGNS_DB)
        cur = conn.cursor()
        
        # Get designs with preview counts and dimensions
        cur.execute("""
            SELECT d.id, d.name, d.price, d.width, d.height, d.tags, d.description, d.image_data, d.image_type,
                   COUNT(dp.id) as preview_count
            FROM designs d
            LEFT JOIN design_previews dp ON d.id = dp.design_id
            GROUP BY d.id
            ORDER BY d.created_at DESC
        """)
        designs = cur.fetchall()
        conn.close()
        
        design_list = []
        for design in designs:
            design_data = {
                "id": design[0],
                "name": design[1],
                "price": float(design[2]),
                "width": design[3] or 0,
                "height": design[4] or 0,
                "tags": design[5] or "",
                "description": design[6] or "",
                "images": [{
                    "data": design[7],
                    "type": design[8] or "image/jpeg",
                    "is_primary": True
                }] if design[7] else [],
                "preview_count": design[9]  # Add preview count
            }
            design_list.append(design_data)
        
        print(f"📊 ADMIN: Retrieved {len(design_list)} designs with dimensions and preview counts")
        return jsonify({"success": True, "designs": design_list})
    except Exception as e:
        print(f"💥 ADMIN GET DESIGNS ERROR: {str(e)}")
        return jsonify({"success": False, "message": str(e)}), 500

@app.route('/admin/designs/<int:design_id>', methods=['DELETE'])
def delete_design(design_id):
    """Delete design - FIXED VERSION"""
    try:
        conn = sqlite3.connect(DESIGNS_DB)
        cur = conn.cursor()
        
        # First check if design exists
        cur.execute("SELECT id FROM designs WHERE id=?", (design_id,))
        if not cur.fetchone():
            conn.close()
            return jsonify({"success": False, "message": "Design not found"}), 404
            
        # Delete design
        cur.execute("DELETE FROM designs WHERE id=?", (design_id,))
        
        conn.commit()
        conn.close()
        
        print(f"✅ DESIGN DELETED SUCCESSFULLY: ID {design_id}")
        return jsonify({"success": True, "message": "Design deleted successfully"})
    except Exception as e:
        print(f"💥 DELETE DESIGN ERROR: {str(e)}")
        return jsonify({"success": False, "message": str(e)}), 500

@app.route('/admin/migrate-designs-pricing', methods=['POST'])
def migrate_designs_pricing():
    """Migrate existing designs to use dimension-based pricing"""
    try:
        conn = sqlite3.connect(DESIGNS_DB)
        cur = conn.cursor()
        
        # First update the schema
        update_designs_schema()
        
        # Get all designs
        cur.execute("SELECT id, name, price FROM designs")
        designs = cur.fetchall()
        
        migrated_count = 0
        for design in designs:
            design_id, name, current_price = design
            
            # Calculate dimensions based on current price (reverse calculation)
            # This is a rough estimate - you might want to set default dimensions
            area = current_price / 10
            width = int(area ** 0.5)  # Square root to get approximate dimensions
            height = width
            
            # Update the design with calculated dimensions
            cur.execute("UPDATE designs SET width=?, height=? WHERE id=?", (width, height, design_id))
            migrated_count += 1
            print(f"📐 Migrated {name}: {width}cm × {height}cm = ₹{current_price}")
        
        conn.commit()
        conn.close()
        
        return jsonify({
            "success": True, 
            "message": f"Migrated {migrated_count} designs to dimension-based pricing",
            "migrated_count": migrated_count
        })
        
    except Exception as e:
        print(f"💥 MIGRATION ERROR: {str(e)}")
        return jsonify({"success": False, "message": str(e)}), 500

# ==================== PREVIEW IMAGE ROUTES ====================

@app.route('/admin/designs/<int:design_id>/previews', methods=['GET'])
def get_design_previews(design_id):
    """Get all preview images for a design"""
    try:
        conn = sqlite3.connect(DESIGNS_DB)
        cur = conn.cursor()
        
        cur.execute("""
            SELECT id, preview_data, preview_type, sort_order 
            FROM design_previews 
            WHERE design_id = ? 
            ORDER BY sort_order
        """, (design_id,))
        previews = cur.fetchall()
        conn.close()
        
        preview_list = []
        for preview in previews:
            preview_list.append({
                "id": preview[0],
                "preview_data": preview[1],
                "preview_type": preview[2],
                "sort_order": preview[3]
            })
        
        return jsonify({"success": True, "previews": preview_list})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

@app.route('/admin/designs/<int:design_id>/previews', methods=['POST'])
def add_design_preview(design_id):
    """Add a preview image to a design"""
    try:
        data = request.get_json()
        preview_data = data.get('preview_data')
        preview_type = data.get('preview_type', 'image/jpeg')
        
        if not preview_data:
            return jsonify({"success": False, "message": "Preview image data is required"}), 400
        
        conn = sqlite3.connect(DESIGNS_DB)
        cur = conn.cursor()
        
        # Get current max sort order
        cur.execute("SELECT MAX(sort_order) FROM design_previews WHERE design_id = ?", (design_id,))
        max_order = cur.fetchone()[0] or -1
        
        # Insert new preview
        cur.execute("""
            INSERT INTO design_previews (design_id, preview_data, preview_type, sort_order)
            VALUES (?, ?, ?, ?)
        """, (design_id, preview_data, preview_type, max_order + 1))
        
        preview_id = cur.lastrowid
        conn.commit()
        conn.close()
        
        return jsonify({"success": True, "preview_id": preview_id, "message": "Preview image added successfully"})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

@app.route('/admin/designs/<int:design_id>/previews/<int:preview_id>', methods=['DELETE'])
def delete_design_preview(design_id, preview_id):
    """Delete a preview image"""
    try:
        conn = sqlite3.connect(DESIGNS_DB)
        cur = conn.cursor()
        
        cur.execute("DELETE FROM design_previews WHERE id = ? AND design_id = ?", (preview_id, design_id))
        
        if cur.rowcount == 0:
            conn.close()
            return jsonify({"success": False, "message": "Preview image not found"}), 404
            
        conn.commit()
        conn.close()
        
        return jsonify({"success": True, "message": "Preview image deleted successfully"})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

# ==================== ADMIN ROUTES ====================

@app.route('/admin/login', methods=['POST'])
def admin_login():
    """Admin login (admin.db) - IMPROVED VERSION"""
    try:
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')
        
        print(f"🔐 ADMIN LOGIN ATTEMPT: {username}")
        
        if not username or not password:
            return jsonify({"success": False, "message": "Username and password are required"}), 400
        
        # Check if admin database file exists
        if not os.path.exists(ADMIN_DB):
            print(f"💥 ADMIN DB FILE NOT FOUND: {ADMIN_DB}")
            return jsonify({"success": False, "message": "Admin database not initialized"}), 500
        
        conn = sqlite3.connect(ADMIN_DB)
        cur = conn.cursor()
        
        # Check if admin_users table exists
        cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='admin_users'")
        table_exists = cur.fetchone()
        
        if not table_exists:
            conn.close()
            print("💥 ADMIN_USERS TABLE NOT FOUND")
            return jsonify({"success": False, "message": "Admin users table not found"}), 500
        
        # Check credentials
        cur.execute("SELECT * FROM admin_users WHERE username=? AND password=?", (username, password))
        admin_user = cur.fetchone()
        conn.close()

        if admin_user:
            print(f"✅ ADMIN LOGIN SUCCESS: {username}")
            
            admin_data = {
                "id": admin_user[0],
                "username": admin_user[1],
                "full_name": admin_user[3],
                "email": admin_user[4],
                "role": admin_user[5],
                "is_admin": True
            }
            return jsonify({"success": True, "user": admin_data})
        else:
            print(f"❌ ADMIN LOGIN FAILED: Invalid credentials for {username}")
            
            # Check if username exists but password is wrong
            conn = sqlite3.connect(ADMIN_DB)
            cur = conn.cursor()
            cur.execute("SELECT username FROM admin_users WHERE username=?", (username,))
            user_exists = cur.fetchone()
            conn.close()
            
            if user_exists:
                return jsonify({"success": False, "message": "Invalid password"}), 401
            else:
                return jsonify({"success": False, "message": "Admin user not found"}), 401
        
    except sqlite3.OperationalError as e:
        print(f"💥 ADMIN DATABASE ERROR: {str(e)}")
        return jsonify({"success": False, "message": "Database connection error"}), 500
    except Exception as e:
        print(f"💥 ADMIN LOGIN ERROR: {str(e)}")
        return jsonify({"success": False, "message": f"Server error: {str(e)}"}), 500
    
@app.route('/admin/users')
def get_all_users():
    """Get all users from users database WITH PASSWORDS"""
    try:
        conn = sqlite3.connect(USERS_DB)
        cur = conn.cursor()
        cur.execute("SELECT * FROM users ORDER BY created_at DESC")
        users = cur.fetchall()
        conn.close()
        
        user_list = []
        for user in users:
            user_list.append({
                "id": user[0],
                "fname": user[1],
                "lname": user[2],
                "email": user[3],
                "username": user[4],
                "password": user[5],  # ADD PASSWORD FIELD
                "address": user[6] or "",
                "mobile": user[7] or "",
                "district": user[8] or "",
                "profile_pic": user[9] or "",
                "created_at": user[10] if len(user) > 10 else ""
            })
        
        print(f"📊 ADMIN: Retrieved {len(user_list)} users from users.db")
        return jsonify({"success": True, "users": user_list})
    except Exception as e:
        print(f"💥 ADMIN GET USERS ERROR: {str(e)}")
        return jsonify({"success": False, "message": str(e)}), 500
    
@app.route('/admin/orders')
def get_all_orders():
    """Get all orders from orders database WITH CUSTOMIZATION FIELDS - FIXED VERSION"""
    try:
        print("📦 ADMIN: Fetching all orders...")
        
        conn = sqlite3.connect(ORDERS_DB)
        cur = conn.cursor()
        
        # First check if table exists and has data
        cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='orders'")
        if not cur.fetchone():
            conn.close()
            return jsonify({"success": True, "orders": [], "message": "Orders table does not exist"})
        
        # Get all orders with proper error handling
        cur.execute("""
            SELECT id, username, design_name, price, quantity, image_url, 
                   placement_position, design_side, design_width, design_height, 
                   custom_requirements, order_date, status, created_at
            FROM orders 
            ORDER BY order_date DESC
        """)
        orders = cur.fetchall()
        conn.close()
        
        order_list = []
        for order in orders:
            order_data = {
                "id": order[0],
                "username": order[1],
                "design_name": order[2],
                "price": float(order[3]) if order[3] else 0,
                "quantity": order[4] or 1,
                "image_url": order[5] or "https://via.placeholder.com/80",
                "placement_position": order[6] if len(order) > 6 and order[6] else '',
                "design_side": order[7] if len(order) > 7 and order[7] else 'front',
                "design_width": order[8] if len(order) > 8 and order[8] else 0,
                "design_height": order[9] if len(order) > 9 and order[9] else 0,
                "custom_requirements": order[10] if len(order) > 10 and order[10] else '',
                "order_date": order[11] or datetime.now().strftime("%Y-%m-%d"),
                "status": order[12] or "Pending",
                "created_at": order[13] if len(order) > 13 else ""
            }
            order_list.append(order_data)
        
        print(f"📊 ADMIN: Retrieved {len(order_list)} orders from orders.db")
        return jsonify({"success": True, "orders": order_list})
        
    except Exception as e:
        print(f"💥 ADMIN GET ORDERS ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({"success": False, "message": str(e)}), 500
    
@app.route('/admin/orders/<int:order_id>', methods=['PUT'])
def update_order_status(order_id):
    """Update order status in orders database"""
    try:
        data = request.get_json()
        new_status = data.get('status')
        
        if not new_status:
            return jsonify({"success": False, "message": "Status is required"}), 400
        
        conn = sqlite3.connect(ORDERS_DB)
        cur = conn.cursor()
        cur.execute("UPDATE orders SET status=? WHERE id=?", (new_status, order_id))
        
        if cur.rowcount == 0:
            conn.close()
            return jsonify({"success": False, "message": "Order not found"}), 404
            
        conn.commit()
        conn.close()
        
        print(f"✅ ADMIN: Updated order {order_id} status to {new_status} in orders.db")
        return jsonify({"success": True, "message": "Order status updated"})
    except Exception as e:
        print(f"💥 ADMIN UPDATE ORDER ERROR: {str(e)}")
        return jsonify({"success": False, "message": str(e)}), 500

@app.route('/admin/orders/<int:order_id>', methods=['DELETE'])
def delete_order(order_id):
    """Delete order from orders database"""
    try:
        conn = sqlite3.connect(ORDERS_DB)
        cur = conn.cursor()
        cur.execute("DELETE FROM orders WHERE id=?", (order_id,))
        
        if cur.rowcount == 0:
            conn.close()
            return jsonify({"success": False, "message": "Order not found"}), 404
            
        conn.commit()
        conn.close()
        
        print(f"✅ ADMIN: Deleted order {order_id} from orders.db")
        return jsonify({"success": True, "message": "Order deleted"})
    except Exception as e:
        print(f"💥 ADMIN DELETE ORDER ERROR: {str(e)}")
        return jsonify({"success": False, "message": str(e)}), 500

@app.route('/admin/stats')
def get_admin_stats():
    """Get admin stats from both databases"""
    try:
        # Users count from users.db
        conn_users = sqlite3.connect(USERS_DB)
        cur_users = conn_users.cursor()
        cur_users.execute("SELECT COUNT(*) FROM users")
        total_users = cur_users.fetchone()[0]
        conn_users.close()
        
        # Orders stats from orders.db
        conn_orders = sqlite3.connect(ORDERS_DB)
        cur_orders = conn_orders.cursor()
        cur_orders.execute("SELECT COUNT(*) FROM orders")
        total_orders = cur_orders.fetchone()[0]
        
        cur_orders.execute("SELECT COUNT(*) FROM orders WHERE status='Pending'")
        pending_orders = cur_orders.fetchone()[0]
        
        cur_orders.execute("SELECT SUM(price * quantity) FROM orders WHERE status='Completed'")
        total_revenue = cur_orders.fetchone()[0] or 0
        conn_orders.close()
        
        stats = {
            "total_users": total_users,
            "total_orders": total_orders,
            "pending_orders": pending_orders,
            "total_revenue": float(total_revenue)
        }
        
        print(f"📊 ADMIN: Stats - Users: {total_users}, Orders: {total_orders}")
        return jsonify({"success": True, "stats": stats})
    except Exception as e:
        print(f"💥 ADMIN GET STATS ERROR: {str(e)}")
        return jsonify({"success": False, "message": str(e)}), 500

# ==================== ANALYTICS ROUTES ====================

@app.route('/admin/analytics')
def get_analytics():
    """Get sales analytics data - SIMPLIFIED VERSION"""
    try:
        print("📊 Generating analytics data...")
        
        conn_orders = sqlite3.connect(ORDERS_DB)
        cur_orders = conn_orders.cursor()
        conn_users = sqlite3.connect(USERS_DB)
        cur_users = conn_users.cursor()
        
        # Get total revenue from completed orders
        cur_orders.execute("SELECT SUM(price * quantity) FROM orders WHERE status='Completed'")
        total_revenue = cur_orders.fetchone()[0] or 0
        
        # Get total orders
        cur_orders.execute("SELECT COUNT(*) FROM orders")
        total_orders = cur_orders.fetchone()[0] or 0
        
        # Get pending orders
        cur_orders.execute("SELECT COUNT(*) FROM orders WHERE status='Pending'")
        pending_orders = cur_orders.fetchone()[0] or 0
        
        # Get new customers (last 30 days)
        cur_users.execute("SELECT COUNT(*) FROM users WHERE date(created_at) >= date('now', '-30 days')")
        new_customers = cur_users.fetchone()[0] or 0
        
        # Get daily revenue for last 7 days using SQLite date functions
        daily_revenue = []
        for i in range(6, -1, -1):  # Last 7 days including today
            date_query = f"date('now', '-{i} days')"
            cur_orders.execute(f"""
                SELECT SUM(price * quantity) 
                FROM orders 
                WHERE status='Completed' AND date(order_date) = {date_query}
            """)
            revenue = cur_orders.fetchone()[0] or 0
            daily_revenue.append({
                "date": (datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d"),
                "revenue": float(revenue)
            })
        
        # Get order status breakdown
        status_breakdown = []
        statuses = ['Completed', 'Pending', 'Processing', 'Ordered']
        for status in statuses:
            cur_orders.execute("SELECT COUNT(*) FROM orders WHERE status=?", (status,))
            order_count = cur_orders.fetchone()[0] or 0
            
            cur_orders.execute("SELECT SUM(price * quantity) FROM orders WHERE status=?", (status,))
            revenue = cur_orders.fetchone()[0] or 0
            
            status_breakdown.append({
                "status": status,
                "order_count": order_count,
                "revenue": float(revenue)
            })
        
        # Get top performing designs
        cur_orders.execute("""
            SELECT design_name, COUNT(*) as order_count, SUM(price * quantity) as revenue
            FROM orders 
            WHERE status='Completed'
            GROUP BY design_name 
            ORDER BY revenue DESC 
            LIMIT 5
        """)
        top_designs_data = cur_orders.fetchall()
        
        top_designs = []
        for design in top_designs_data:
            top_designs.append({
                "name": design[0],
                "order_count": design[1],
                "revenue": float(design[2]) if design[2] else 0
            })
        
        # Calculate metrics
        average_order_value = 0
        if total_orders > 0:
            average_order_value = round(total_revenue / total_orders, 2)
        
        conversion_rate = 0
        total_customers_response = get_all_users()
        total_customers_data = total_customers_response.get_json()
        total_customers = len(total_customers_data['users']) if total_customers_data['success'] else 0
        
        if total_customers > 0:
            conversion_rate = round((total_orders / total_customers) * 100, 1)
        
        conn_orders.close()
        conn_users.close()
        
        # Simplified analytics data without complex period comparisons
        analytics_data = {
            "revenue": {
                "total": float(total_revenue),
                "current_month": float(total_revenue),  # Simplified
                "change_percentage": 0  # Simplified for now
            },
            "orders": {
                "total": total_orders,
                "change_percentage": 0  # Simplified for now
            },
            "customers": {
                "new_customers": new_customers,
                "change_percentage": 0  # Simplified for now
            },
            "daily_revenue": daily_revenue,
            "status_breakdown": status_breakdown,
            "top_designs": top_designs,
            "metrics": {
                "average_order_value": average_order_value,
                "conversion_rate": conversion_rate
            }
        }
        
        print(f"✅ ANALYTICS: Generated data - Revenue: ₹{total_revenue}, Orders: {total_orders}")
        return jsonify({"success": True, "analytics": analytics_data})
        
    except Exception as e:
        print(f"💥 ANALYTICS ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({"success": False, "message": str(e)}), 500

# ==================== DEBUG & UTILITY ROUTES ====================

@app.route('/debug/users')
def debug_users():
    conn = sqlite3.connect(USERS_DB)
    cur = conn.cursor()
    cur.execute("SELECT * FROM users")
    users = cur.fetchall()
    conn.close()
    
    user_list = []
    for user in users:
        user_list.append({
            "id": user[0],
            "fname": user[1],
            "lname": user[2],
            "email": user[3],
            "username": user[4],
            "password": "" + (user[5][-4:] if user[5] and len(user[5]) > 4 else "*"),
            "address": user[6],
            "mobile": user[7],
            "district": user[8],
            "profile_pic_length": len(user[9]) if user[9] else 0,
            "created_at": user[10] if len(user) > 10 else ""
        })
    
    return jsonify({
        "database": "users.db",
        "users": user_list, 
        "total_users": len(users)
    })

@app.route('/debug/cart/<username>')
def debug_cart(username):
    conn = sqlite3.connect(USERS_DB)
    cur = conn.cursor()
    cur.execute("SELECT * FROM user_cart WHERE username=?", (username,))
    cart_items = cur.fetchall()
    conn.close()
    
    cart_list = []
    for item in cart_items:
        cart_list.append({
            "id": item[0],
            "username": item[1],
            "design_name": item[2],
            "price": item[3],
            "quantity": item[4],
            "image_url": item[5],
            "placement_position": item[6] if len(item) > 6 else '',
            "design_side": item[7] if len(item) > 7 else 'front',
            "design_width": item[8] if len(item) > 8 else 0,
            "design_height": item[9] if len(item) > 9 else 0,
            "custom_requirements": item[10] if len(item) > 10 else ''
        })
    
    return jsonify({
        "database": "users.db",
        "cart": cart_list,
        "total_items": len(cart_items)
    })

@app.route('/debug/orders')
def debug_orders():
    conn = sqlite3.connect(ORDERS_DB)
    cur = conn.cursor()
    cur.execute("SELECT * FROM orders")
    orders = cur.fetchall()
    conn.close()
    
    order_list = []
    for order in orders:
        order_list.append({
            "id": order[0],
            "username": order[1],
            "design_name": order[2],
            "price": order[3],
            "quantity": order[4],
            "image_url": order[5],
            "placement_position": order[6] if len(order) > 6 else '',
            "design_side": order[7] if len(order) > 7 else 'front',
            "design_width": order[8] if len(order) > 8 else 0,
            "design_height": order[9] if len(order) > 9 else 0,
            "custom_requirements": order[10] if len(order) > 10 else '',
            "order_date": order[11],
            "status": order[12]
        })
    
    return jsonify({
        "database": "orders.db",
        "orders": order_list,
        "total_orders": len(orders)
    })

@app.route('/health')
def health():
    return jsonify({
        "status": "OK", 
        "message": "Fine Graphics Server is running",
        "databases": {
            "users_db": "users_new.db (user accounts + cart + wishlist)",
            "orders_db": "orders_new.db (all orders)",
            "admin_db": "admin_new.db (admin accounts)",
            "designs_db": "designs_fresh.db (design catalog with automatic pricing)"
        },
        "features": {
            "automatic_pricing": "Price = Width × Height × 10",
            "dimension_based": "No manual price entry required"
        },
        "endpoints": {
            "cart": {
                "saveCart": "/saveCart",
                "getCart": "/getCart/<username>",
                "clearCart": "/clearCart/<username>"
            },
            "wishlist": {
                "saveWishlist": "/saveWishlist",
                "getWishlist": "/getWishlist/<username>"
            },
            "sync": {
                "syncUserData": "/syncUserData",
                "getUserData": "/getUserData/<username>"
            },
            "designs": {
                "getDesigns": "/getDesigns",
                "adminDesigns": "/admin/designs"
            },
            "admin": {
                "migrate_pricing": "/admin/migrate-designs-pricing"
            }
        }
    })

# ==================== DATABASE RESET ROUTES ====================

@app.route('/admin/reset-designs-db', methods=['POST'])
def reset_designs_db():
    """Reset designs database (for development only) - FIXED VERSION"""
    try:
        # Remove existing designs database file
        if os.path.exists(DESIGNS_DB):
            os.remove(DESIGNS_DB)
            print(f"🗑 Removed existing designs database: {DESIGNS_DB}")
        
        # Reinitialize designs database
        success = init_designs_db()
        
        if success:
            return jsonify({"success": True, "message": "Designs database reset successfully"})
        else:
            return jsonify({"success": False, "message": "Failed to reset designs database"}), 500
            
    except Exception as e:
        print(f"💥 RESET DESIGNS DB ERROR: {str(e)}")
        return jsonify({"success": False, "message": str(e)}), 500

@app.route('/debug/databases')
def debug_databases():
    """Debug all databases status"""
    databases_info = {}
    
    # Check each database
    databases = {
        "users": USERS_DB,
        "orders": ORDERS_DB,
        "admin": ADMIN_DB,
        "designs": DESIGNS_DB
    }
    
    for db_name, db_file in databases.items():
        try:
            db_exists = os.path.exists(db_file)
            tables = []
            
            if db_exists:
                conn = sqlite3.connect(db_file)
                cur = conn.cursor()
                cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
                tables = [table[0] for table in cur.fetchall()]
                conn.close()
            
            databases_info[db_name] = {
                "file": db_file,
                "exists": db_exists,
                "tables": tables
            }
            
        except Exception as e:
            databases_info[db_name] = {
                "file": db_file,
                "exists": False,
                "error": str(e)
            }
    
    return jsonify(databases_info)

if __name__ == '__main__':
    # Initialize fresh databases
    init_databases()
    
    # Update designs schema to include dimensions
    print("🔄 Updating designs schema with dimensions...")
    update_designs_schema()
    
    # IMMEDIATE VERIFICATION - Check if designs tables were created
    print("🔍 Verifying designs database creation...")
    try:
        conn = sqlite3.connect(DESIGNS_DB)
        cur = conn.cursor()
        cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cur.fetchall()
        
        # Check if dimensions columns exist
        cur.execute("PRAGMA table_info(designs)")
        columns = [col[1] for col in cur.fetchall()]
        conn.close()
        
        table_names = [table[0] for table in tables]
        print(f"📊 Designs DB Tables Found: {table_names}")
        print(f"📐 Designs Table Columns: {columns}")
        
        if 'designs' not in table_names:
            print("🚨 CRITICAL: Required tables missing! Forcing reinitialization...")
            success = init_designs_db()
            if success:
                print("✅ Designs database reinitialized successfully!")
            else:
                print("❌ Failed to reinitialize designs database!")
    except Exception as e:
        print(f"🚨 Designs DB verification failed: {e}")
    
    print("\n" + "="*60)
    print("🚀 FINE GRAPHICS SERVER STARTED")
    print("="*60)
    print("🎯 NEW FEATURE: Automatic Price Calculation")
    print("   💰 Price = Width × Height × 10")
    print("   📐 No more manual price entry!")
    print("🌐 Server URL: http://localhost:5000")
    print("🔍 Health Check: http://localhost:5000/health")
    print("\n📊 SEPARATE DATABASES:")
    print("   👥 Users Database: users_new.db (accounts + cart + wishlist)")
    print("   📦 Orders Database: orders_new.db (all orders)")
    print("   👑 Admin Database: admin_new.db (admin accounts)")
    print("   🎨 Designs Database: designs_fresh.db (AUTOMATIC PRICING: width × height × 10)")
    print("\n🛒 FEATURES:")
    print("   💾 Cart saved to database (works on any device)")
    print("   ❤️ Wishlist saved to database (works on any device)")
    print("   🔄 Automatic sync between local storage and database")
    print("   🎨 AUTOMATIC PRICING: Dimension-based pricing (width × height × 10)")
    print("\n🔐 ADMIN CREDENTIALS:")
    print("   📧 Username: admin")
    print("   🔑 Password: admin123")
    print("\n🔧 Debug Routes:")
    print("   🛒 User Cart: http://localhost:5000/debug/cart/<username>")
    print("   ❤️ User Wishlist: http://localhost:5000/debug/wishlist/<username>")
    print("   📦 All Orders: http://localhost:5000/debug/orders")
    print("   🎨 Designs Structure: http://localhost:5000/debug/designs-detailed")
    print("   🔄 Migrate Pricing: POST http://localhost:5000/admin/migrate-designs-pricing")
    print("="*60 + "\n")
    
    app.run(debug=True, host='0.0.0.0', port=5000, use_reloader=False)