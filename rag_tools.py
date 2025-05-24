from typing import Optional, List, Dict, Any
from langchain_core.tools import tool
from langchain_core.runnables import RunnableConfig
import logging

from rag_search import get_product_rag

logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger(__name__)

@tool
def semantic_product_search(
    query: str,
    category: Optional[str] = None,
    material: Optional[str] = None,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    min_stock: Optional[int] = None,
    top_k: int = 5
) -> List[Dict[str, Any]]:
    """
    Searches for products using semantic understanding of the query and product descriptions.
    
    Use this tool when the user is looking for products with specific features, cultural significance,
    crafting techniques, or other detailed attributes that might not be captured by simple keyword matching.
    
    Examples:
    - "Tìm sản phẩm làm quà tặng cho người nước ngoài" (Find products suitable as gifts for foreigners)
    - "Sản phẩm nào có ý nghĩa văn hóa đặc biệt?" (Which products have special cultural significance?)
    - "Tôi cần đồ trang trí phòng khách phong cách truyền thống" (I need traditional-style living room decorations)
    
    Args:
        query: The natural language query describing what the user is looking for
        category: Optional category filter (e.g., "Nón", "Giỏ", "Tranh")
        material: Optional material filter (e.g., "Tre", "Gỗ", "Mây")
        min_price: Minimum price in VND
        max_price: Maximum price in VND
        min_stock: Minimum stock quantity available
        top_k: Number of results to return (default: 5)
        
    Returns:
        A list of matching products with their details and relevance scores
    """
    logger.info(f"Semantic product search: {query}")
    
    # Prepare filters
    filters = {}
    if category:
        filters["category"] = category
    if material:
        filters["material"] = material
    if min_price is not None:
        filters["min_price"] = min_price
    if max_price is not None:
        filters["max_price"] = max_price
    if min_stock is not None:
        filters["min_stock"] = min_stock
    
    # Get RAG instance and search
    rag = get_product_rag()
    # Use hybrid search for better results
    results = rag.search(query, top_k=top_k, filters=filters, search_type="hybrid")
    
    # Format results for better readability
    formatted_results = []
    for product in results:
        formatted_results.append({
            "product_id": product["product_id"],
            "name": product["name"],
            "category": product["category"],
            "material": product["material"],
            "price": product["price"],
            "stock_quantity": product["stock_quantity"],
            "origin_location": product["origin_location"],
            "relevance_score": f"{product['similarity']:.2f}",
            "description_preview": product["content"].split('\n\n')[5].replace('Mô tả: ', '')[:100] + '...' if len(product["content"].split('\n\n')) > 5 else ""
        })
    
    return formatted_results

@tool
def get_product_cultural_context(product_id: int) -> Dict[str, Any]:
    """
    Retrieves detailed cultural context and crafting information about a specific product.
    
    Use this tool when the user wants to learn more about the cultural significance, origin,
    or traditional crafting techniques of a specific product.
    
    Examples:
    - "Tell me more about the cultural significance of product 7"
    - "What's special about how product 3 is made?"
    - "I want to know more about the history of this nón lá"
    
    Args:
        product_id: The ID of the product to get detailed information for
        
    Returns:
        Detailed information about the product's cultural context and crafting techniques
    """
    logger.info(f"Getting cultural context for product ID: {product_id}")
    
    # Get RAG instance and retrieve product
    rag = get_product_rag()
    product = rag.get_product_by_id(product_id)
    
    if not product:
        return {"error": f"Không tìm thấy sản phẩm với ID {product_id}"}
    
    # Return cultural context
    return {
        "product_id": product["product_id"],
        "name": product["name"],
        "origin_location": product["origin_location"],
        "crafting_technique": product["crafting_technique"],
        "cultural_significance": product["cultural_significance"],
        "dimensions": product["dimensions"],
        "care_instructions": product["care_instructions"]
    }

@tool
def get_similar_products(product_id: int, top_k: int = 3) -> List[Dict[str, Any]]:
    """
    Finds products similar to the specified product.
    
    Use this tool when the user wants to see alternatives or similar products to one they're viewing.
    
    Examples:
    - "Show me products similar to product 5"
    - "What other products are like this one?"
    - "Do you have anything similar to this nón lá?"
    
    Args:
        product_id: The ID of the reference product
        top_k: Number of similar products to return (default: 3)
        
    Returns:
        A list of similar products with their details
    """
    logger.info(f"Finding similar products to ID: {product_id}")
    
    # Get RAG instance
    rag = get_product_rag()
    
    # Get similar products
    similar_products = rag.get_similar_products(product_id, top_k=top_k)
    
    # Format results
    formatted_results = []
    for product in similar_products:
        formatted_results.append({
            "product_id": product["product_id"],
            "name": product["name"],
            "category": product["category"],
            "material": product["material"],
            "price": product["price"],
            "stock_quantity": product["stock_quantity"],
            "origin_location": product["origin_location"],
            "similarity_score": f"{product['similarity']:.2f}",
            "description_preview": product["content"].split('\n\n')[5].replace('Mô tả: ', '')[:100] + '...' if len(product["content"].split('\n\n')) > 5 else ""
        })
    
    return formatted_results
