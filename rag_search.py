import os
import sqlite3
from typing import List, Dict, Any, Optional, Union, Callable
from dotenv import load_dotenv
import logging
import pickle
from pathlib import Path
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Define paths for persisting data
VECTOR_STORE_PATH = os.getenv("VECTOR_STORE_PATH", "data/vector_store")
TFIDF_PATH = os.getenv("TFIDF_PATH", "data/tfidf_model.pkl")
PRODUCT_DATA_PATH = os.getenv("PRODUCT_DATA_PATH", "data/product_data.pkl")

class ProductRAG:
    """Retrieval Augmented Generation for product metadata with hybrid search capabilities."""
    
    _instance = None
    
    @classmethod
    def get_instance(cls):
        """Get singleton instance to avoid recreating embeddings."""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
    
    def __init__(self):
        """Initialize the RAG system with Google Generative AI embeddings."""
        # Get DB_PATH with proper path handling
        self.db_path = os.getenv("DB_PATH")
        if not self.db_path:
            # Default to a database in the current directory
            self.db_path = os.path.join(os.getcwd(), "data", "handicraft.sqlite")
            logger.warning(f"DB_PATH not set, using default: {self.db_path}")
        
        # Normalize path to handle backslashes correctly
        self.db_path = os.path.normpath(self.db_path)
            
        self.embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001")
        self.vector_store = None
        self.product_data = []
        self.initialized = False
        self.tfidf_vectorizer = None
        self.tfidf_matrix = None
        self.product_texts = []
        
        # Create directories if they don't exist
        os.makedirs(os.path.dirname(VECTOR_STORE_PATH), exist_ok=True)
        os.makedirs(os.path.dirname(TFIDF_PATH), exist_ok=True)
        os.makedirs(os.path.dirname(PRODUCT_DATA_PATH), exist_ok=True)
    
    def _get_connection(self) -> sqlite3.Connection:
        """Get a database connection."""
        logger.info(f"Connecting to database: {self.db_path}")
        if not os.path.exists(self.db_path):
            logger.error(f"Database file does not exist: {self.db_path}")
            raise FileNotFoundError(f"Database file not found: {self.db_path}")
        return sqlite3.connect(self.db_path)
    
    def _extract_products(self) -> List[Dict[str, Any]]:
        """Extract all products with their metadata from the database."""
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("""
                SELECT 
                    product_id, 
                    name, 
                    category, 
                    material, 
                    price, 
                    stock_quantity, 
                    description,
                    origin_location,
                    crafting_technique,
                    cultural_significance,
                    dimensions,
                    care_instructions,
                    tags
                FROM products
            """)
            
            columns = [col[0] for col in cursor.description]
            products = [dict(zip(columns, row)) for row in cursor.fetchall()]
            return products
        except Exception as e:
            logger.error(f"Error extracting products: {str(e)}")
            raise
        finally:
            cursor.close()
            conn.close()
    
    def _create_documents(self, products: List[Dict[str, Any]]) -> List[Document]:
        """Convert products to Document objects for vector storage."""
        documents = []
        self.product_texts = []
        
        for product in products:
            # Create a rich text representation for embedding
            content = f"""Sản phẩm: {product['name']}

Danh mục: {product['category']}
Chất liệu: {product['material']}
Giá: {product['price']} đồng
Số lượng trong kho: {product['stock_quantity']}

Mô tả: {product['description']}

Xuất xứ: {product['origin_location']}
Kỹ thuật chế tác: {product['crafting_technique']}
Ý nghĩa văn hóa: {product['cultural_significance']}
Kích thước: {product['dimensions']}
Hướng dẫn bảo quản: {product['care_instructions']}
Từ khóa: {product['tags']}"""
            
            # Store text for TF-IDF
            self.product_texts.append(content)
            
            # Create metadata for filtering and additional context
            metadata = {
                "product_id": product["product_id"],
                "name": product["name"],
                "category": product["category"],
                "material": product["material"],
                "price": product["price"],
                "stock_quantity": product["stock_quantity"],
                "origin_location": product["origin_location"],
                "tags": product["tags"]
            }
            
            documents.append(Document(page_content=content, metadata=metadata))
        
        return documents
    
    def _setup_tfidf(self):
        """Set up TF-IDF vectorizer for keyword search."""
        self.tfidf_vectorizer = TfidfVectorizer(
            lowercase=True,
            stop_words='english',  # We could add Vietnamese stop words here
            ngram_range=(1, 2)  # Use unigrams and bigrams
        )
        self.tfidf_matrix = self.tfidf_vectorizer.fit_transform(self.product_texts)
        logger.info("TF-IDF vectorizer initialized")
        
        # Save TF-IDF model to disk
        with open(TFIDF_PATH, 'wb') as f:
            pickle.dump((self.tfidf_vectorizer, self.tfidf_matrix, self.product_texts), f)
        logger.info(f"TF-IDF model saved to {TFIDF_PATH}")
    
    def _load_tfidf(self) -> bool:
        """Load TF-IDF model from disk if available."""
        if os.path.exists(TFIDF_PATH):
            try:
                with open(TFIDF_PATH, 'rb') as f:
                    self.tfidf_vectorizer, self.tfidf_matrix, self.product_texts = pickle.load(f)
                logger.info(f"TF-IDF model loaded from {TFIDF_PATH}")
                return True
            except Exception as e:
                logger.error(f"Error loading TF-IDF model: {str(e)}")
        return False
    
    def _save_product_data(self):
        """Save product data to disk."""
        with open(PRODUCT_DATA_PATH, 'wb') as f:
            pickle.dump(self.product_data, f)
        logger.info(f"Product data saved to {PRODUCT_DATA_PATH}")
    
    def _load_product_data(self) -> bool:
        """Load product data from disk if available."""
        if os.path.exists(PRODUCT_DATA_PATH):
            try:
                with open(PRODUCT_DATA_PATH, 'rb') as f:
                    self.product_data = pickle.load(f)
                logger.info(f"Product data loaded from {PRODUCT_DATA_PATH}")
                return True
            except Exception as e:
                logger.error(f"Error loading product data: {str(e)}")
        return False
    
    def initialize(self, force_reload=False):
        """Initialize or reload the vector store with product data."""
        if self.initialized and not force_reload:
            return
        
        try:
            logger.info("Initializing product RAG system...")
            
            # Check if we can load from disk first
            vector_store_exists = os.path.exists(VECTOR_STORE_PATH)
            product_data_loaded = self._load_product_data()
            tfidf_loaded = self._load_tfidf()
            
            # If all data is available and no force reload, load from disk
            if vector_store_exists and product_data_loaded and tfidf_loaded and not force_reload:
                # Load vector store from disk
                self.vector_store = FAISS.load_local(
                    VECTOR_STORE_PATH,
                    self.embeddings,
                    allow_dangerous_deserialization=True
                )
                logger.info(f"Vector store loaded from {VECTOR_STORE_PATH}")
                self.initialized = True
                logger.info("Product RAG system initialized from disk")
                return
            
            # Otherwise, rebuild everything
            # Extract products from database
            self.product_data = self._extract_products()
            logger.info(f"Extracted {len(self.product_data)} products from database")
            
            # Save product data
            self._save_product_data()
            
            # Convert to documents
            documents = self._create_documents(self.product_data)
            
            # Create vector store
            self.vector_store = FAISS.from_documents(documents, self.embeddings)
            
            # Save vector store to disk
            self.vector_store.save_local(VECTOR_STORE_PATH)
            logger.info(f"Vector store saved to {VECTOR_STORE_PATH}")
            
            # Set up TF-IDF for keyword search
            self._setup_tfidf()
            
            self.initialized = True
            logger.info("Product RAG system initialized successfully")
        except Exception as e:
            logger.error(f"Error initializing RAG system: {str(e)}")
            raise
    
    def _apply_filters(self, results: List[Dict[str, Any]], filters: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Apply filters to search results."""
        if not filters:
            return results
            
        filtered_results = []
        for product in results:
            include = True
            
            for key, value in filters.items():
                if key == "min_price" and product.get("price", 0) < value:
                    include = False
                    break
                elif key == "max_price" and product.get("price", float('inf')) > value:
                    include = False
                    break
                elif key == "min_stock" and product.get("stock_quantity", 0) < value:
                    include = False
                    break
                elif key in product and product[key] != value:
                    include = False
                    break
            
            if include:
                filtered_results.append(product)
                
        return filtered_results
    
    def _keyword_search(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """Perform keyword-based search using TF-IDF."""
        if not self.initialized:
            self.initialize()
            
        # Transform query to TF-IDF space
        query_vector = self.tfidf_vectorizer.transform([query])
        
        # Calculate cosine similarity
        similarities = cosine_similarity(query_vector, self.tfidf_matrix)[0]
        
        # Get top-k indices
        top_indices = similarities.argsort()[-top_k:][::-1]
        
        results = []
        for idx in top_indices:
            if similarities[idx] > 0.0:  # Only include if there's some similarity
                product = self.product_data[idx].copy()
                product["similarity"] = float(similarities[idx])
                product["content"] = self.product_texts[idx]
                results.append(product)
                
        return results
    
    def _semantic_search(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """Perform semantic search using embeddings."""
        if not self.initialized:
            self.initialize()
            
        # Search the vector store
        search_results = self.vector_store.similarity_search_with_score(query, k=top_k)
        
        results = []
        for doc, score in search_results:
            # Convert score to similarity (FAISS returns L2 distance)
            similarity = 1.0 / (1.0 + score)
            
            # Find the corresponding product
            product_id = doc.metadata["product_id"]
            product = next((p.copy() for p in self.product_data if p["product_id"] == product_id), None)
            
            if product:
                product["similarity"] = similarity
                product["content"] = doc.page_content
                results.append(product)
                
        return results
    
    def search(self, query: str, top_k: int = 5, filters: Optional[Dict[str, Any]] = None, 
               search_type: str = "hybrid", semantic_weight: float = 0.7) -> List[Dict[str, Any]]:
        """Search for products based on semantic similarity, keywords, and optional filters.
        
        Args:
            query: The search query in natural language
            top_k: Number of results to return
            filters: Optional filters like category, material, price range, etc.
            search_type: Type of search to perform ("semantic", "keyword", or "hybrid")
            semantic_weight: Weight for semantic search results in hybrid search (0.0-1.0)
            
        Returns:
            List of matching products with similarity scores
        """
        if not self.initialized:
            self.initialize()
        
        try:
            results = []
            
            if search_type == "semantic" or search_type == "hybrid":
                semantic_results = self._semantic_search(query, top_k=top_k*2 if search_type == "hybrid" else top_k)
                
                if search_type == "semantic":
                    results = semantic_results
                    
            if search_type == "keyword" or search_type == "hybrid":
                keyword_results = self._keyword_search(query, top_k=top_k*2 if search_type == "hybrid" else top_k)
                
                if search_type == "keyword":
                    results = keyword_results
            
            # Combine results for hybrid search
            if search_type == "hybrid":
                # Create a dictionary to store combined results
                combined_results = {}
                
                # Add semantic results with weight
                for product in semantic_results:
                    product_id = product["product_id"]
                    combined_results[product_id] = {
                        **product,
                        "similarity": product["similarity"] * semantic_weight
                    }
                
                # Add or update with keyword results
                for product in keyword_results:
                    product_id = product["product_id"]
                    if product_id in combined_results:
                        # Update existing entry
                        combined_results[product_id]["similarity"] += product["similarity"] * (1 - semantic_weight)
                    else:
                        # Add new entry
                        combined_results[product_id] = {
                            **product,
                            "similarity": product["similarity"] * (1 - semantic_weight)
                        }
                
                # Convert back to list and sort by similarity
                results = list(combined_results.values())
            
            # Sort by similarity score
            results = sorted(results, key=lambda x: x["similarity"], reverse=True)
            
            # Apply filters
            if filters:
                results = self._apply_filters(results, filters)
            
            # Return top-k results
            return results[:top_k]
            
        except Exception as e:
            logger.error(f"Error searching products: {str(e)}")
            return []
    
    def get_product_by_id(self, product_id: int) -> Optional[Dict[str, Any]]:
        """Get a product by its ID."""
        if not self.initialized:
            self.initialize()
        
        for product in self.product_data:
            if product["product_id"] == product_id:
                return product
        
        return None
    
    def get_similar_products(self, product_id: int, top_k: int = 5) -> List[Dict[str, Any]]:
        """Get products similar to the given product ID."""
        if not self.initialized:
            self.initialize()
            
        product = self.get_product_by_id(product_id)
        if not product:
            return []
            
        # Use product name and description as query
        query = f"{product['name']} {product['description']}"
        
        # Exclude the original product from results
        results = self.search(query, top_k=top_k+1)
        return [p for p in results if p["product_id"] != product_id][:top_k]
    
    def refresh_data(self):
        """Refresh data from database and rebuild indices."""
        logger.info("Refreshing RAG data from database...")
        self.initialize(force_reload=True)
        logger.info("RAG data refreshed successfully")

# Function to get pre-initialized instance
def get_product_rag():
    """Get the singleton ProductRAG instance."""
    return ProductRAG.get_instance()

if __name__ == "__main__":
    # Set the DB_PATH explicitly for testing
    os.environ["DB_PATH"] = os.path.join(os.getcwd(), "data", "handicraft.sqlite")
    
    product_rag = ProductRAG.get_instance()
    product_rag.initialize()
    print(product_rag.search("Tìm sản phẩm làm quà tặng cho người nước ngoài"))