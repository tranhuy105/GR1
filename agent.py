from typing import Annotated, Dict, Any, List
from datetime import datetime
from typing_extensions import TypedDict
import os
from langchain_ollama import ChatOllama
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.runnables import Runnable, RunnableConfig
from langgraph.graph.message import add_messages, AnyMessage
from langchain_core.messages import AIMessage
from tools import (
    fetch_user_order_information,
    lookup_store_policy,
    view_cart,
    add_to_cart,
    update_cart_item,
    clear_cart,
    place_order,
    cancel_order
)
from rag_tools import (
    semantic_product_search,
    get_product_cultural_context,
    get_similar_products
)
import logging

from dotenv import load_dotenv, find_dotenv
from utils import debug_log, clean_deepseek_response

# Enhanced debug dotenv loading
debug_log("=== DOTENV LOADING ===")
env_file = find_dotenv()
debug_log(f"Found .env file at: {env_file}")

# Load with verbose to see errors
loaded = load_dotenv(verbose=True, override=True)
debug_log(f"Dotenv loaded successfully: {loaded}")

# Print all related environment variables
debug_log("=== ENVIRONMENT VARIABLES ===")
debug_log(f"DB_PATH: {os.getenv('DB_PATH', 'NOT FOUND')}")
debug_log(f"USE_OLLAMA: {os.getenv('USE_OLLAMA', 'NOT FOUND')}")
debug_log(f"LLM_TEMPERATURE: {os.getenv('LLM_TEMPERATURE', 'NOT FOUND')}")
debug_log(f"LLM_MODEL: {os.getenv('LLM_MODEL', 'NOT FOUND')}")

logger = logging.getLogger(__name__)

class State(TypedDict):
    messages: Annotated[list[AnyMessage], add_messages]
    user_info: List[Dict[str, Any]]

class Assistant:
    def __init__(self, runnable: Runnable):
        self.runnable = runnable

    def __call__(self, state: State, config: RunnableConfig):
        debug_log("=== ASSISTANT CALL ===")
        debug_log("Input state messages count", len(state.get("messages", [])))
        
        # Let the LLM handle all requests directly
        while True:
            result = self.runnable.invoke(state)
            
            debug_log("LLM Result", {
                "type": type(result).__name__,
                "has_content": bool(result.content),
                "content_preview": result.content[:200] if result.content else "No content",
                "has_tool_calls": bool(result.tool_calls),
                "tool_calls_count": len(result.tool_calls) if result.tool_calls else 0
            })
            
            # Clean Deepseek responses
            if isinstance(result, AIMessage) and result.content:
                original_content = result.content
                cleaned_content = clean_deepseek_response(result.content)
                if cleaned_content != original_content:
                    result.content = cleaned_content
                    debug_log("Content was cleaned", {
                        "original": original_content[:100],
                        "cleaned": cleaned_content[:100]
                    })
            
            if not result.tool_calls and (
                not result.content
                or isinstance(result.content, list)
                and not result.content[0].get("text")
            ):
                debug_log("Empty response, requesting real output", level="WARN")
                messages = state["messages"] + [("user", "Respond with a real output.")]
                state = {**state, "messages": messages}
            else:
                break
                
        debug_log("Final assistant result", {
            "content": result.content[:100] if result.content else "No content",
            "tool_calls": len(result.tool_calls) if result.tool_calls else 0
        })
        
        return {"messages": result}

def getLLm():
    """Get LLM instance based on environment configuration with enhanced Deepseek support"""
    # Safe boolean parsing
    use_ollama_str = os.getenv("USE_OLLAMA", "0").strip().lower()
    use_ollama = use_ollama_str in ["1", "true", "yes", "on"]
    
    try:
        temperature = float(os.getenv("LLM_TEMPERATURE", "0.2"))
    except (ValueError, TypeError):
        temperature = 0.2
        debug_log(f"Invalid LLM_TEMPERATURE value, using default: {temperature}", level="WARN")
    
    llm_model = os.getenv("LLM_MODEL", "gemini-pro").strip()
    
    debug_log(f"Using {'Ollama' if use_ollama else 'Google Generative AI'} with temperature {temperature}")
    debug_log(f"Model: {llm_model}")
    
    logger.info(f"Using {'Ollama' if use_ollama else 'Google Generative AI'} with temperature {temperature}")
    logger.info(f"Model: {llm_model}")
    
    if use_ollama:  
        ollama_config = {
            "model": llm_model,
            "temperature": temperature,
        }
        
        # Filter None values
        ollama_config = {k: v for k, v in ollama_config.items() if v is not None}
        
        debug_log("Ollama configuration", ollama_config)
        
        return ChatOllama(**ollama_config)
    else:
        debug_log("Configuring Google Generative AI")
        return ChatGoogleGenerativeAI(model=llm_model, temperature=temperature)

# Define tool groups with enhanced logging
debug_log("=== TOOL CONFIGURATION ===")

safe_tools = [
    fetch_user_order_information,
    lookup_store_policy,
    view_cart,
    semantic_product_search,
    get_product_cultural_context,
    get_similar_products
]

sensitive_tools = [
    add_to_cart,
    update_cart_item,
    place_order,
    cancel_order,
    clear_cart
]

debug_log(f"Safe tools: {len(safe_tools)}")
debug_log(f"Sensitive tools: {len(sensitive_tools)}")

# Remove the module-level LLM instantiation and assistant_runnable
# These should be created by the EnhancedChatBot class to ensure consistency