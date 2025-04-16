
from typing import Dict, Any, List, Optional
import sqlite3
import os
import logging

logger = logging.getLogger(__name__)
class Database:
    """Handle all SQL operations for the handicraft store."""
    
    def __init__(self):
        self.db_path = os.getenv('DB_PATH')
    
    def _get_connection(self) -> sqlite3.Connection:
        return sqlite3.connect(self.db_path)
    
    def search_products(
        self,
        query: Optional[str] = None,
        category: Optional[str] = None,
        material: Optional[str] = None,
        min_price: Optional[float] = None,
        max_price: Optional[float] = None,
        min_stock: Optional[int] = None,
        sort_by_price: Optional[str] = None,
        limit: int = 20
    ) -> List[Dict]:
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            query_sql = "SELECT product_id, name, category, material, price, stock_quantity, description FROM products WHERE 1 = 1"
            params = []
            
            if category:
                query_sql += " AND LOWER(category) = LOWER(?)"
                params.append(category)
            if material:
                query_sql += " AND LOWER(material) = LOWER(?)"
                params.append(material)
            if min_price:
                query_sql += " AND price >= ?"
                params.append(min_price)
            if max_price:
                query_sql += " AND price <= ?"
                params.append(max_price)
            if min_stock:
                query_sql += " AND stock_quantity >= ?"
                params.append(min_stock)
            if sort_by_price:
                query_sql += " ORDER BY price " + ("ASC" if sort_by_price.lower() == "asc" else "DESC")
            
            query_sql += " LIMIT ?"
            params.append(limit)
            
            cursor.execute(query_sql, params)
            rows = cursor.fetchall()
            results = [
                {
                    "product_id": row[0],
                    "name": row[1],
                    "category": row[2],
                    "material": row[3],
                    "price": row[4],
                    "stock_quantity": row[5],
                    "description": row[6]
                }
                for row in rows
            ]
            return results
        except Exception as e:
            logger.error(f"Error searching products: {str(e)}")
            raise
        finally:
            cursor.close()
            conn.close()
    
    def get_orders(self, customer_id: str) -> List[Dict]:
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("""
                SELECT 
                    o.order_id, o.order_date, o.status, o.total_amount,
                    p.name as product_name, oi.quantity, oi.price_at_time
                FROM orders o
                JOIN order_items oi ON o.order_id = oi.order_id
                JOIN products p ON oi.product_id = p.product_id
                WHERE o.customer_id = ?
            """, (customer_id,))
            rows = cursor.fetchall()
            results = [
                {
                    "order_id": row[0],
                    "order_date": row[1],
                    "status": row[2],
                    "total_amount": row[3],
                    "product_name": row[4],
                    "quantity": row[5],
                    "price_at_time": row[6]
                }
                for row in rows
            ]
            return results
        except Exception as e:
            logger.error(f"Error fetching orders: {str(e)}")
            raise
        finally:
            cursor.close()
            conn.close()
    
    def get_cart(self, customer_id: str) -> Optional[Dict]:
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT cart_id FROM carts WHERE customer_id = ?", (customer_id,))
            cart = cursor.fetchone()
            if not cart:
                return None
            
            cart_id = cart[0]
            cursor.execute("""
                SELECT ci.product_id, p.name, ci.quantity, ci.price_at_time
                FROM cart_items ci
                JOIN products p ON ci.product_id = p.product_id
                WHERE ci.cart_id = ?
            """, (cart_id,))
            items = [
                {
                    "product_id": row[0],
                    "name": row[1],
                    "quantity": row[2],
                    "price": row[3]
                }
                for row in cursor.fetchall()
            ]
            return {"cart_id": cart_id, "items": items}
        except Exception as e:
            logger.error(f"Error getting cart: {str(e)}")
            raise
        finally:
            cursor.close()
            conn.close()
    
    def get_or_create_cart(self, customer_id: str) -> int:
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT cart_id FROM carts WHERE customer_id = ?", (customer_id,))
            cart = cursor.fetchone()
            if cart:
                return cart[0]
            
            cursor.execute("INSERT INTO carts (customer_id) VALUES (?)", (customer_id,))
            cart_id = cursor.lastrowid
            conn.commit()
            return cart_id
        except Exception as e:
            conn.rollback()
            logger.error(f"Error creating cart: {str(e)}")
            raise
        finally:
            cursor.close()
            conn.close()
    
    def get_product(self, product_id: int) -> Optional[Dict]:
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT product_id, name, price, stock_quantity FROM products WHERE product_id = ?", (product_id,))
            row = cursor.fetchone()
            if not row:
                return None
            return {
                "product_id": row[0],
                "name": row[1],
                "price": row[2],
                "stock_quantity": row[3]
            }
        except Exception as e:
            logger.error(f"Error getting product: {str(e)}")
            raise
        finally:
            cursor.close()
            conn.close()
    
    def add_to_cart(self, customer_id: str, product_id: int, quantity: int) -> str:
        if quantity <= 0:
            return "Số lượng phải lớn hơn 0."
        
        product = self.get_product(product_id)
        if not product:
            return f"Sản phẩm với ID {product_id} không tồn tại."
        
        if product["stock_quantity"] < quantity:
            return f"Sản phẩm {product['name']} chỉ còn {product['stock_quantity']} cái, không đủ {quantity} cái."
        
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            cart_id = self.get_or_create_cart(customer_id)
            
            # Check if item exists in cart
            cursor.execute("SELECT quantity FROM cart_items WHERE cart_id = ? AND product_id = ?", (cart_id, product_id))
            existing = cursor.fetchone()
            if existing:
                new_quantity = existing[0] + quantity
                if product["stock_quantity"] < new_quantity:
                    return f"Sản phẩm {product['name']} chỉ còn {product['stock_quantity']} cái, không đủ {new_quantity} cái."
                cursor.execute("""
                    UPDATE cart_items 
                    SET quantity = ?, price_at_time = ?
                    WHERE cart_id = ? AND product_id = ?
                """, (new_quantity, product["price"], cart_id, product_id))
            else:
                cursor.execute("""
                    INSERT INTO cart_items (cart_id, product_id, quantity, price_at_time)
                    VALUES (?, ?, ?, ?)
                """, (cart_id, product_id, quantity, product["price"]))
            
            cursor.execute("UPDATE carts SET updated_at = CURRENT_TIMESTAMP WHERE cart_id = ?", (cart_id,))
            conn.commit()
            
            return f"Đã thêm {quantity} {product['name']} vào giỏ hàng. {self.view_cart(customer_id)}"
        except Exception as e:
            conn.rollback()
            logger.error(f"Error adding to cart: {str(e)}")
            return f"Lỗi khi thêm vào giỏ hàng: {str(e)}"
        finally:
            cursor.close()
            conn.close()
    
    def update_cart_item(self, customer_id: str, product_id: int, quantity: int) -> str:
        if quantity < 0:
            return "Số lượng không thể âm."
        
        cart = self.get_cart(customer_id)
        if not cart:
            return "Giỏ hàng hiện tại trống."
        
        cart_id = cart["cart_id"]
        item_exists = False
        for item in cart["items"]:
            if item["product_id"] == product_id:
                item_exists = True
                break
        if not item_exists:
            return f"Không tìm thấy sản phẩm với ID {product_id} trong giỏ hàng."
        
        product = self.get_product(product_id)
        if not product:
            return f"Sản phẩm với ID {product_id} không tồn tại."
        
        if quantity > 0 and product["stock_quantity"] < quantity:
            return f"Sản phẩm {product['name']} chỉ còn {product['stock_quantity']} cái, không đủ {quantity} cái."
        
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            if quantity == 0:
                cursor.execute("DELETE FROM cart_items WHERE cart_id = ? AND product_id = ?", (cart_id, product_id))
                result = f"Đã xóa {product['name']} khỏi giỏ hàng."
            else:
                cursor.execute("""
                    UPDATE cart_items 
                    SET quantity = ?, price_at_time = ?
                    WHERE cart_id = ? AND product_id = ?
                """, (quantity, product["price"], cart_id, product_id))
                result = f"Đã cập nhật {product['name']} thành {quantity} cái."
            
            cursor.execute("UPDATE carts SET updated_at = CURRENT_TIMESTAMP WHERE cart_id = ?", (cart_id,))
            conn.commit()
            
            return f"{result} {self.view_cart(customer_id)}"
        except Exception as e:
            conn.rollback()
            logger.error(f"Error updating cart item: {str(e)}")
            return f"Lỗi khi cập nhật giỏ hàng: {str(e)}"
        finally:
            cursor.close()
            conn.close()
    
    def view_cart(self, customer_id: str) -> str:
        cart = self.get_cart(customer_id)
        if not cart or not cart["items"]:
            return "Giỏ hàng hiện tại trống."
        
        total = sum(item["quantity"] * item["price"] for item in cart["items"])
        cart_summary = "\n".join(
            f"- {item['name']} (ID: {item['product_id']}, x{item['quantity']}, {item['quantity'] * item['price']:,}đ)"
            for item in cart["items"]
        )
        return f"Giỏ hàng hiện tại:\n{cart_summary}\nTổng tiền: {total:,}đ"
    
    def clear_cart(self, customer_id: str) -> str:
        cart = self.get_cart(customer_id)
        if not cart:
            return "Giỏ hàng hiện tại trống."
        
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("DELETE FROM cart_items WHERE cart_id = ?", (cart["cart_id"],))
            cursor.execute("DELETE FROM carts WHERE cart_id = ?", (cart["cart_id"],))
            conn.commit()
            return "Đã xóa toàn bộ giỏ hàng."
        except Exception as e:
            conn.rollback()
            logger.error(f"Error clearing cart: {str(e)}")
            return f"Lỗi khi xóa giỏ hàng: {str(e)}"
        finally:
            cursor.close()
            conn.close()
    
    def place_order(self, customer_id: str) -> str:
        cart = self.get_cart(customer_id)
        if not cart or not cart["items"]:
            return "Giỏ hàng trống. Vui lòng thêm sản phẩm trước khi đặt hàng."
        
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            # Verify stock
            for item in cart["items"]:
                cursor.execute("SELECT stock_quantity FROM products WHERE product_id = ?", (item["product_id"],))
                stock = cursor.fetchone()[0]
                if stock < item["quantity"]:
                    return f"Sản phẩm {item['name']} chỉ còn {stock} cái, không đủ {item['quantity']} cái."
            
            total_amount = sum(item["quantity"] * item["price"] for item in cart["items"])
            cursor.execute(
                "INSERT INTO orders (customer_id, status, total_amount) VALUES (?, ?, ?)",
                (customer_id, "Đang xử lý", total_amount)
            )
            order_id = cursor.lastrowid
            
            for item in cart["items"]:
                cursor.execute(
                    "INSERT INTO order_items (order_id, product_id, quantity, price_at_time) VALUES (?, ?, ?, ?)",
                    (order_id, item["product_id"], item["quantity"], item["price"])
                )
                cursor.execute(
                    "UPDATE products SET stock_quantity = stock_quantity - ? WHERE product_id = ?",
                    (item["quantity"], item["product_id"])
                )
            
            cursor.execute("DELETE FROM cart_items WHERE cart_id = ?", (cart["cart_id"],))
            cursor.execute("DELETE FROM carts WHERE cart_id = ?", (cart["cart_id"],))
            
            conn.commit()
            return f"Đã tạo đơn hàng ID {order_id}. Tổng tiền: {total_amount:,}đ"
        except Exception as e:
            conn.rollback()
            logger.error(f"Error placing order: {str(e)}")
            return f"Lỗi khi tạo đơn hàng: {str(e)}"
        finally:
            cursor.close()
            conn.close()
    
    def cancel_order(self, customer_id: str, order_id: int) -> str:
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                "SELECT status FROM orders WHERE order_id = ? AND customer_id = ?", 
                (order_id, customer_id)
            )
            result = cursor.fetchone()
            if not result:
                return f"Không tìm thấy đơn hàng với ID {order_id}."
            if result[0] == "Đã giao":
                return "Không thể hủy đơn hàng đã giao. Vui lòng sử dụng chính sách đổi trả."
            
            cursor.execute("SELECT product_id, quantity FROM order_items WHERE order_id = ?", (order_id,))
            order_items = cursor.fetchall()
            for product_id, quantity in order_items:
                cursor.execute(
                    "UPDATE products SET stock_quantity = stock_quantity + ? WHERE product_id = ?",
                    (quantity, product_id)
                )
            
            cursor.execute("UPDATE orders SET status = 'Đã hủy' WHERE order_id = ?", (order_id,))
            conn.commit()
            return f"Đã hủy đơn hàng {order_id} và cập nhật lại kho hàng."
        except Exception as e:
            conn.rollback()
            logger.error(f"Error cancelling order: {str(e)}")
            return f"Lỗi khi hủy đơn hàng: {str(e)}"
        finally:
            cursor.close()
            conn.close()