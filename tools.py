import os
import sqlite3
from typing import Optional, List, Dict
from dotenv import load_dotenv
import logging
from langchain_core.tools import tool
from langchain_core.runnables import RunnableConfig
from constants import POLICIES, CATEGORIES, MATERIALS
from db import Database

logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger(__name__)

load_dotenv()

# Initialize Database instance
db = Database()

def get_user_id_from_config(config: RunnableConfig) -> str:
    """Extracts the customer ID from the provided configuration."""
    configuration = config.get("configurable", {})
    customer_id = configuration.get("customer_id", None)
    if not customer_id:
        raise ValueError("Không tìm thấy thông tin khách hàng.")
    return customer_id

@tool
def fetch_user_order_information(config: RunnableConfig) -> List[Dict]:
    """
    Retrieves all orders and their associated items for a specific customer.

    Use this tool when the user wants to review their order history, check past purchases, or inquire about previous transactions.
    Example: "Can you show me my order history?" or "What items did I order last month?"

    Args:
        config: Configuration object containing the customer ID.

    Returns:
        A list of dictionaries containing order details, including order ID, date, items, and total cost.
    """
    customer_id = get_user_id_from_config(config)
    return db.get_orders(customer_id)

@tool
def get_product_details(product_id: int) -> Dict:
    """
    Fetches detailed information about a specific product based on its ID.

    Use this tool when the user asks for details about a specific product, such as its name, price, material, or stock status.
    Example: "Tell me about product ID 123" or "What are the details of this item?"

    Args:
        product_id: The unique ID of the product to retrieve details for.

    Returns:
        A dictionary containing product details like name, price, category, material, and stock quantity.
    """
    return db.get_product(product_id)

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
    """
    Searches for handicraft products based on various filters like query, category, material, price range, and stock.

    Use this tool when the user is looking for products matching specific criteria, such as searching for items by name, category, material, or price range.
    Example: "Find me bamboo baskets under 500,000 VND" or "Show me all wooden statues available."

    Args:
        query: A free-text search term to match product names or descriptions (e.g., "basket" or "handmade").
        category: The product category to filter by. Must be one of: {', '.join(CATEGORIES)}.
        material: The material type to filter by. Must be one of: {', '.join(MATERIALS)}.
        min_price: The minimum price in VND (e.g., 100000 for 100,000 VND).
        max_price: The maximum price in VND (e.g., 500000 for 500,000 VND).
        min_stock: The minimum stock quantity available (e.g., 1 to show only in-stock items).
        sort_by_price: Sort order for price, either 'asc' (cheapest first) or 'desc' (most expensive first).
        limit: Maximum number of results to return (default is 20).

    Returns:
        A list of dictionaries containing details of matching products, including name, price, category, material, and stock.

    Raises:
        ValueError: If category or material is not in the allowed list.
    """
    logger.warn(f"search_products called with: query={query}, category={category}, material={material}, sort_by_price={sort_by_price}")

    # Validate category
    if category and category not in CATEGORIES:
        raise ValueError(f"Category must be one of: {', '.join(CATEGORIES)}")

    # Validate material
    if material and material not in MATERIALS:
        raise ValueError(f"Material must be one of: {', '.join(MATERIALS)}")

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
    """
    Retrieves store policy information based on the user's query about store policies.

    Use this tool when the user asks about store policies, such as shipping, returns, payment methods, warranty, bulk orders, or custom services.
    The LLM should interpret the query and map it to one of the following policy categories: shipping, returns, payment, warranty, order_process, bulk_sales, custom_services.
    Example: "What is your return policy?" → LLM maps to "returns" → returns the return policy.
             "How much is shipping?" → LLM maps to "shipping" → returns the shipping policy.
             "Can I get a custom order?" → LLM maps to "custom_services" → returns the custom services policy.

    Args:
        query: The user's question about store policies (e.g., "What is the shipping cost?" or "How do I return an item?").
               The LLM should pass a query that aligns with one of the policy categories.

    Returns:
        A string containing the relevant policy information or a prompt for more specific details if the query is unclear or no matching policy is found.
    """
    # Normalize query to lowercase for consistency
    query = query.lower().strip()

    # Available policy keys from POLICIES (e.g., 'shipping', 'returns', 'payment', etc.)
    valid_policies = list(POLICIES.keys())

    # Check if the query directly matches a policy key (LLM should ideally pass a clean policy key)
    if query in valid_policies:
        return POLICIES[query]

    # Fallback for unclear queries
    return f"""Xin lỗi, tôi không chắc chắn về chính sách bạn đang hỏi. Bạn có thể hỏi cụ thể hơn về một trong các chính sách sau:
- {', '.join(valid_policies)}"""    

@tool
def view_cart(config: RunnableConfig) -> str:
    """
    Displays the current contents of the user's shopping cart.

    Use this tool when the user wants to see what items are in their cart, including quantities and total cost.
    Example: "What's in my cart?" or "Show me my shopping cart."

    Args:
        config: Configuration object containing the customer ID.

    Returns:
        A string summarizing the cart contents, including product names, quantities, and total price.
    """
    customer_id = get_user_id_from_config(config)
    return db.view_cart(customer_id)

@tool
def add_to_cart(product_id: int, quantity: int, config: RunnableConfig) -> str:
    """
    Adds a specified quantity of a product to the user's shopping cart.

    Use this tool when the user wants to add a product to their cart.
    Example: "Add 2 bamboo baskets to my cart" or "I want to buy product ID 123."

    Args:
        product_id: The ID of the product to add to the cart.
        quantity: The number of items to add (must be positive).
        config: Configuration object containing the customer ID.

    Returns:
        A confirmation message indicating the product was added or an error if the operation failed.
    """
    customer_id = get_user_id_from_config(config)
    return db.add_to_cart(customer_id, product_id, quantity)

@tool
def update_cart_item(product_id: int, quantity: int, config: RunnableConfig) -> str:
    """
    Updates the quantity of a specific product in the user's shopping cart or removes it if quantity is set to 0.

    Use this tool when the user wants to change the quantity of an item in their cart or remove it.
    Example: "Change the quantity of product ID 123 to 3" or "Remove this item from my cart."

    Args:
        product_id: The ID of the product to update.
        quantity: The new quantity (set to 0 to remove the item).
        config: Configuration object containing the customer ID.

    Returns:
        A confirmation message indicating the cart was updated or an error if the operation failed.
    """
    customer_id = get_user_id_from_config(config)
    return db.update_cart_item(customer_id, product_id, quantity)

@tool
def clear_cart(config: RunnableConfig) -> str:
    """
    Removes all items from the user's shopping cart.

    Use this tool when the user wants to empty their cart completely.
    Example: "Clear my cart" or "Remove everything from my shopping cart."

    Args:
        config: Configuration object containing the customer ID.

    Returns:
        A confirmation message indicating the cart was cleared.
    """
    customer_id = get_user_id_from_config(config)
    return db.clear_cart(customer_id)

@tool
def place_order(config: RunnableConfig) -> str:
    """
    Places an order based on the current contents of the user's shopping cart.

    Use this tool when the user is ready to complete their purchase and place an order.
    Example: "Place my order" or "I want to checkout now."

    Args:
        config: Configuration object containing the customer ID.

    Returns:
        A confirmation message with the order details or an error if the operation failed.
    """
    customer_id = get_user_id_from_config(config)
    return db.place_order(customer_id)

@tool
def cancel_order(order_id: int, config: RunnableConfig) -> str:
    """
    Cancels an existing order based on the order ID.

    Use this tool when the user wants to cancel a specific order they previously placed.
    Example: "Cancel my order with ID 456" or "I want to cancel my last order."

    Args:
        order_id: The ID of the order to cancel.
        config: Configuration object containing the customer ID.

    Returns:
        A confirmation message indicating the order was canceled or an error if the operation failed.
    """
    customer_id = get_user_id_from_config(config)
    return db.cancel_order(customer_id, order_id)