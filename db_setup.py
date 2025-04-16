# import os
# import sqlite3
# import getpass
# from datetime import datetime
# from random import choice, randint, uniform
# from dotenv import load_dotenv

# from constants import CATEGORIES, MATERIALS, ORDER_STATUSES

# load_dotenv()

# def _set_env(var: str):
#     if not os.environ.get(var):
#         os.environ[var] = getpass.getpass(f"{var}: ")

# _set_env("GOOGLE_API_KEY")

# def create_schema(conn):
#     """Create database schema for products, orders, order_items, carts, and cart_items."""
#     cursor = conn.cursor()
#     cursor.executescript("""
#     CREATE TABLE IF NOT EXISTS products (
#         product_id INTEGER PRIMARY KEY,
#         name TEXT,
#         category TEXT,
#         material TEXT,
#         price DECIMAL,
#         stock_quantity INTEGER,
#         description TEXT
#     );

#     CREATE TABLE IF NOT EXISTS orders (
#         order_id INTEGER PRIMARY KEY,
#         customer_id TEXT,
#         order_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
#         status TEXT,
#         total_amount DECIMAL
#     );

#     CREATE TABLE IF NOT EXISTS order_items (
#         order_id INTEGER,
#         product_id INTEGER,
#         quantity INTEGER,
#         price_at_time DECIMAL,
#         FOREIGN KEY (order_id) REFERENCES orders(order_id),
#         FOREIGN KEY (product_id) REFERENCES products(product_id)
#     );

#     CREATE TABLE IF NOT EXISTS carts (
#         cart_id INTEGER PRIMARY KEY,
#         customer_id TEXT,
#         created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
#         updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
#     );

#     CREATE TABLE IF NOT EXISTS cart_items (
#         cart_id INTEGER,
#         product_id INTEGER,
#         quantity INTEGER,
#         price_at_time DECIMAL,
#         FOREIGN KEY (cart_id) REFERENCES carts(cart_id),
#         FOREIGN KEY (product_id) REFERENCES products(product_id)
#     );
#     """)
#     conn.commit()

# def generate_products(num_products=100):
#     """Generate diverse, realistic products using constants."""
#     category_materials = {
#         "Nón": ["Lá cọ", "Vải"],
#         "Giỏ": ["Tre", "Mây", "Vải"],
#         "Đồ Gia Dụng": ["Gỗ", "Tre", "Mây"],
#         "Tranh": ["Vải", "Gỗ"],
#         "Tượng": ["Gỗ", "Đá"]
#     }
    
#     price_ranges = {
#         "Nón": (50000, 200000),
#         "Giỏ": (100000, 300000),
#         "Đồ Gia Dụng": (150000, 500000),
#         "Tranh": (500000, 2000000),
#         "Tượng": (500000, 3000000)
#     }
    
#     name_templates = {
#         "Nón": ["Nón Lá {style}", "Nón {material} {style}", "Nón Thêu {style}"],
#         "Giỏ": ["Giỏ Đan {material}", "Giỏ {style} {material}", "Giỏ Quà {material}"],
#         "Đồ Gia Dụng": ["Khay {material} {style}", "Hộp {material} {style}", "Đĩa {material} {style}"],
#         "Tranh": ["Tranh Thêu {style}", "Tranh {material} {style}", "Tranh Phong Cảnh {style}"],
#         "Tượng": ["Tượng {material} {style}", "Tượng Phật {style}", "Tượng Nghệ Thuật {style}"]
#     }
    
#     styles = ["Truyền Thống", "Huế", "Bắc Bộ", "Nam Bộ", "Hoa Văn", "Cổ Điển", "Hiện Đại"]
#     origins = ["làng nghề Huế", "Bắc Kạn", "Phú Thọ", "Đồng Nai", "Hà Nội"]
    
#     products = []
#     used_names = set()
    
#     for i in range(1, num_products + 1):
#         category = choice(CATEGORIES)
#         material = choice(category_materials[category])
#         min_price, max_price = price_ranges[category]
        
#         while True:
#             style = choice(styles)
#             name_template = choice(name_templates[category])
#             name = name_template.format(material=material, style=style)
#             if name not in used_names:
#                 used_names.add(name)
#                 break
        
#         price = round(uniform(min_price, max_price), -3)
#         stock = randint(5, 50)
        
#         origin = choice(origins)
#         use_case = choice(["quà tặng", "trang trí nhà cửa", "sử dụng hàng ngày", "lễ hội"])
#         description = f"Sản phẩm thủ công {name.lower()} từ {material.lower()}, chế tác tại {origin}. Phù hợp cho {use_case}."
        
#         products.append((i, name, category, material, price, stock, description))
    
#     return products

# def generate_orders(num_orders=5):
#     """Generate sample orders."""
#     orders = []
#     dates = ["2024-03-15", "2024-03-16", "2025-04-01", "2025-04-10", "2025-04-15"]
#     for i in range(1, num_orders + 1):
#         customer_id = f"CUST00{randint(1, 3)}"
#         order_date = choice(dates)
#         status = choice(ORDER_STATUSES)
#         total_amount = 0
#         orders.append((i, customer_id, order_date, status, total_amount))
#     return orders

# def generate_order_items(orders, products, max_items_per_order=3):
#     """Generate order items linking orders to products."""
#     order_items = []
#     for order_id, _, _, _, _ in orders:
#         num_items = randint(1, max_items_per_order)
#         selected_products = [choice(products) for _ in range(num_items)]
#         total_amount = 0
#         for product in selected_products:
#             product_id, _, _, _, price, _, _ = product
#             quantity = randint(1, 5)
#             total_amount += price * quantity
#             order_items.append((order_id, product_id, quantity, price))
#         orders[order_id - 1] = (
#             orders[order_id - 1][0],
#             orders[order_id - 1][1],
#             orders[order_id - 1][2],
#             orders[order_id - 1][3],
#             total_amount
#         )
#     return order_items, orders

# def generate_cart_items(products, customer_id="CUST001"):
#     """Generate sample cart items for testing."""
#     carts = [(1, customer_id, datetime.now(), datetime.now())]
#     cart_items = []
#     num_items = randint(1, 3)
#     selected_products = [choice(products) for _ in range(num_items)]
#     for product in selected_products:
#         product_id, _, _, _, price, _, _ = product
#         quantity = randint(1, 5)
#         cart_items.append((1, product_id, quantity, price))
#     return carts, cart_items

# def insert_data(conn, products, orders, order_items, carts, cart_items):
#     """Insert generated data into the database."""
#     cursor = conn.cursor()
#     cursor.executemany(
#         "INSERT INTO products VALUES (?, ?, ?, ?, ?, ?, ?)",
#         products
#     )
#     cursor.executemany(
#         "INSERT INTO orders VALUES (?, ?, ?, ?, ?)",
#         orders
#     )
#     cursor.executemany(
#         "INSERT INTO order_items VALUES (?, ?, ?, ?)",
#         order_items
#     )
#     cursor.executemany(
#         "INSERT INTO carts VALUES (?, ?, ?, ?)",
#         carts
#     )
#     cursor.executemany(
#         "INSERT INTO cart_items VALUES (?, ?, ?, ?)",
#         cart_items
#     )
#     conn.commit()

# def setup_database(clear_existing=False):
#     """Set up the database with schema and sample data."""
#     db_file = os.getenv("DB_PATH")
#     if clear_existing and os.path.exists(db_file):
#         os.remove(db_file)
    
#     conn = sqlite3.connect(db_file)
    
#     create_schema(conn)
    
#     products = generate_products(num_products=100)
#     orders = generate_orders(num_orders=5)
#     order_items, orders = generate_order_items(orders, products, max_items_per_order=3)
#     carts, cart_items = generate_cart_items(products, customer_id="CUST001")
    
#     insert_data(conn, products, orders, order_items, carts, cart_items)
    
#     conn.close()
#     print("Database set up successfully!")
#     return db_file

# if __name__ == "__main__":
#     db = setup_database(clear_existing=True)

