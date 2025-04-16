import os
import sqlite3
from typing import Optional, List, Dict
from dotenv import load_dotenv
import re
import logging
from langchain_core.tools import tool
from langchain_core.runnables import RunnableConfig
from intent_matching import find_best_intent, POLICY_INTENTS, PRODUCT_SEARCH_INTENTS, get_intent_score
from constants import POLICIES, CATEGORIES, MATERIALS
from random import choice
from db import Database
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

load_dotenv()

# Initialize Database instance
db = Database()

def get_user_id_from_config(config: RunnableConfig) -> str:
    configuration = config.get("configurable", {})
    customer_id = configuration.get("customer_id", None)
    if not customer_id:
        raise ValueError("Không tìm thấy thông tin khách hàng.")
    return customer_id

@tool
def fetch_user_order_information(config: RunnableConfig) -> List[Dict]:
    """Fetch all orders and their items for a given customer."""
    customer_id = get_user_id_from_config(config)
    return db.get_orders(customer_id)

@tool
def search_products(
    query: Optional[str] = None,
    category: Optional[str] = None,
    material: Optional[str] = None,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    min_stock: Optional[int] = None,
    sort_by_price: Optional[str] = None,
    limit: int = 20,
) -> List[Dict]:
    """Search for handicraft products with stock and price sorting."""
    logger.debug(f"search_products called with: query={query}, category={category}, material={material}, sort_by_price={sort_by_price}")
    
    if query:
        intent_scores = sorted(
            [(intent, get_intent_score(query, config.get("keywords", {}), config.get("patterns", [])))
             for intent, config in PRODUCT_SEARCH_INTENTS.items()],
            key=lambda x: x[1],
            reverse=True
        )
        logger.debug(f"Intent scores: {intent_scores}")
        
        for intent, score in intent_scores:
            if score < 0.5:
                continue
            if intent == "by_quantity":
                quantity_match = re.search(r'(\d+)\s*(?:cái|sản phẩm|món)', query, re.IGNORECASE)
                if quantity_match:
                    min_stock = int(quantity_match.group(1))
                elif "một vài" in query.lower() or "vài" in query.lower():
                    min_stock = min_stock or 3
                logger.debug(f"Parsed min_stock: {min_stock}")
            if intent == "by_price":
                price_matches = re.findall(r'(\d+)(?:k|nghìn|triệu|\$)?', query)
                range_match = re.search(r'(?:từ|tầm)\s*(\d+)(?:k|nghìn).*(?:đến|to)\s*(\d+)(?:k|nghìn)', query, re.IGNORECASE)
                if range_match:
                    min_price = float(range_match.group(1)) * 1000
                    max_price = float(range_match.group(2)) * 1000
                elif len(price_matches) >= 2:
                    min_price = float(price_matches[0]) * 1000
                    max_price = float(price_matches[1]) * 1000
                elif len(price_matches) == 1:
                    if "dưới" in query.lower():
                        max_price = float(price_matches[0]) * 1000
                    else:
                        min_price = float(price_matches[0]) * 1000
                if "rẻ nhất" in query.lower():
                    sort_by_price = "asc"
                elif "đắt nhất" in query.lower():
                    sort_by_price = "desc"
                logger.debug(f"Price: min={min_price}, max={max_price}, sort={sort_by_price}")
            if intent == "by_category" and not category:
                for cat in CATEGORIES:
                    if cat.lower() in query.lower():
                        category = cat
                        break
                if "đồ trang trí" in query.lower():
                    category = category or choice(["Tranh", "Tượng"])
                logger.debug(f"Category set to: {category}")
            if intent == "by_material" and not material:
                for mat in MATERIALS:
                    if mat.lower() in query.lower() or f"{mat.lower()} tự nhiên" in query.lower():
                        material = mat
                        break
                logger.debug(f"Material set to: {material}")
            if intent == "by_vague":
                logger.debug("Vague query detected; keeping params broad")
    
    return db.search_products(
        query=query,
        category=category,
        material=material,
        min_price=min_price,
        max_price=max_price,
        min_stock=min_stock,
        sort_by_price=sort_by_price,
        limit=limit
    )

@tool
def lookup_store_policy(query: str) -> str:
    """Look up store policies regarding orders, shipping, returns, etc."""
    best_intent, score = find_best_intent(query, POLICY_INTENTS)
    if best_intent and best_intent in POLICIES:
        return POLICIES[best_intent]
    return """Xin lỗi, tôi không chắc chắn về chính sách bạn đang hỏi. 
Bạn có thể cho tôi biết cụ thể hơn về:
- Chính sách vận chuyển
- Chính sách đổi trả
- Phương thức thanh toán
- Chính sách bảo hành
- Quy trình đặt hàng
- Chính sách bán sỉ
- Dịch vụ theo yêu cầu"""

@tool
def view_cart(config: RunnableConfig) -> str:
    """View the current shopping cart."""
    customer_id = get_user_id_from_config(config)
    return db.view_cart(customer_id)

@tool
def add_to_cart(product_id: int, quantity: int, config: RunnableConfig) -> str:
    """Add a product to the cart."""
    customer_id = get_user_id_from_config(config)
    return db.add_to_cart(customer_id, product_id, quantity)

@tool
def update_cart_item(product_id: int, quantity: int, config: RunnableConfig) -> str:
    """Update the quantity of a product in the cart."""
    customer_id = get_user_id_from_config(config)
    return db.update_cart_item(customer_id, product_id, quantity)

@tool
def clear_cart(config: RunnableConfig) -> str:
    """Clear the entire cart."""
    customer_id = get_user_id_from_config(config)
    return db.clear_cart(customer_id)

@tool
def place_order(config: RunnableConfig) -> str:
    """Place an order based on the current cart."""
    customer_id = get_user_id_from_config(config)
    return db.place_order(customer_id)

@tool
def cancel_order(order_id: int, config: RunnableConfig) -> str:
    """Cancel an existing order."""
    customer_id = get_user_id_from_config(config)
    return db.cancel_order(customer_id, order_id)