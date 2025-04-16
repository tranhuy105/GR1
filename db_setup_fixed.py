
import os
import sqlite3
import getpass
from datetime import datetime
from dotenv import load_dotenv

from constants import CATEGORIES, MATERIALS, ORDER_STATUSES

load_dotenv()

def _set_env(var: str):
    if not os.environ.get(var):
        os.environ[var] = getpass.getpass(f"{var}: ")

_set_env("GOOGLE_API_KEY")

def create_schema(conn):
    """Create database schema for products, orders, order_items, carts, and cart_items."""
    cursor = conn.cursor()
    cursor.executescript("""
    CREATE TABLE IF NOT EXISTS products (
        product_id INTEGER PRIMARY KEY,
        name TEXT,
        category TEXT,
        material TEXT,
        price DECIMAL,
        stock_quantity INTEGER,
        description TEXT
    );

    CREATE TABLE IF NOT EXISTS orders (
        order_id INTEGER PRIMARY KEY,
        customer_id TEXT,
        order_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        status TEXT,
        total_amount DECIMAL
    );

    CREATE TABLE IF NOT EXISTS order_items (
        order_id INTEGER,
        product_id INTEGER,
        quantity INTEGER,
        price_at_time DECIMAL,
        FOREIGN KEY (order_id) REFERENCES orders(order_id),
        FOREIGN KEY (product_id) REFERENCES products(product_id)
    );

    CREATE TABLE IF NOT EXISTS carts (
        cart_id INTEGER PRIMARY KEY,
        customer_id TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS cart_items (
        cart_id INTEGER,
        product_id INTEGER,
        quantity INTEGER,
        price_at_time DECIMAL,
        FOREIGN KEY (cart_id) REFERENCES carts(cart_id),
        FOREIGN KEY (product_id) REFERENCES products(product_id)
    );
    """)
    conn.commit()

def generate_products():
    """Generate fixed, deterministic products."""
    products = [
        (1, "Nón Lá Cổ Điển", "Nón", "Lá cọ", 112000, 45, "Nón lá truyền thống từ làng nghề Huế, phù hợp quà tặng."),
        (2, "Nón Thêu Hoa Sen", "Nón", "Vải", 188000, 28, "Nón thêu hoa sen tinh tế, trang trí hoặc sử dụng."),
        (3, "Giỏ Đan Mây Huế", "Giỏ", "Mây", 250000, 15, "Giỏ mây đan thủ công từ Huế, dùng đựng đồ."),
        (4, "Giỏ Tre Quà Tặng", "Giỏ", "Tre", 300000, 20, "Giỏ tre đẹp, phù hợp làm quà tặng."),
        (5, "Khay Gỗ Truyền Thống", "Đồ Gia Dụng", "Gỗ", 200000, 30, "Khay gỗ dùng trong gia đình, bền đẹp."),
        (6, "Hộp Mây Trang Trí", "Đồ Gia Dụng", "Mây", 350000, 25, "Hộp mây thủ công, trang trí nhà cửa."),
        (7, "Tranh Thêu Phong Cảnh", "Tranh", "Vải", 500000, 10, "Tranh thêu phong cảnh Việt Nam, treo tường."),
        (8, "Tranh Gỗ Đồng Quê", "Tranh", "Gỗ", 800000, 8, "Tranh gỗ khắc đồng quê, nghệ thuật cao cấp."),
        (9, "Tượng Phật Gỗ", "Tượng", "Gỗ", 1000000, 5, "Tượng Phật gỗ thủ công, tâm linh và trang trí."),
        (10, "Tượng Đá Nghệ Thuật", "Tượng", "Đá", 1500000, 3, "Tượng đá chạm khắc, độc đáo và sang trọng.")
    ]
    return products

def generate_orders():
    """Generate fixed, deterministic orders."""
    orders = [
        (1, "CUST001", "2025-04-01", "Đang xử lý", 560000),  # 5 Nón Lá Cổ Điển
        (2, "CUST001", "2025-04-10", "Đã giao", 600000),     # 2 Giỏ Tre Quà Tặng
    ]
    return orders

def generate_order_items(orders):
    """Generate fixed order items."""
    order_items = [
        (1, 1, 5, 112000),  # Order 1: 5 Nón Lá Cổ Điển
        (2, 4, 2, 300000),  # Order 2: 2 Giỏ Tre Quà Tặng
    ]
    return order_items, orders

def generate_cart_items():
    """Generate empty cart for testing."""
    carts = [(1, "CUST001", datetime.now(), datetime.now())]
    cart_items = []  # Start empty, let tests add items
    return carts, cart_items

def insert_data(conn, products, orders, order_items, carts, cart_items):
    """Insert generated data into the database."""
    cursor = conn.cursor()
    cursor.executemany(
        "INSERT INTO products VALUES (?, ?, ?, ?, ?, ?, ?)",
        products
    )
    cursor.executemany(
        "INSERT INTO orders VALUES (?, ?, ?, ?, ?)",
        orders
    )
    cursor.executemany(
        "INSERT INTO order_items VALUES (?, ?, ?, ?)",
        order_items
    )
    cursor.executemany(
        "INSERT INTO carts VALUES (?, ?, ?, ?)",
        carts
    )
    cursor.executemany(
        "INSERT INTO cart_items VALUES (?, ?, ?, ?)",
        cart_items
    )
    conn.commit()

def setup_database(clear_existing=False):
    """Set up the database with schema and deterministic data."""
    db_file = os.getenv("DB_PATH")
    if clear_existing and os.path.exists(db_file):
        os.remove(db_file)
    
    conn = sqlite3.connect(db_file)
    
    create_schema(conn)
    
    products = generate_products()
    orders = generate_orders()
    order_items, orders = generate_order_items(orders)
    carts, cart_items = generate_cart_items()
    
    insert_data(conn, products, orders, order_items, carts, cart_items)
    
    conn.close()
    print("Database set up successfully!")
    return db_file

if __name__ == "__main__":
    db = setup_database(clear_existing=True)