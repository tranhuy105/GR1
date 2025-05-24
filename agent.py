from typing import Annotated, Dict, Any, List
from datetime import datetime
from typing_extensions import TypedDict
import os
from langchain_ollama import ChatOllama
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.runnables import Runnable, RunnableConfig
from langgraph.graph.message import add_messages, AnyMessage
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

logger = logging.getLogger(__name__)

class State(TypedDict):
    messages: Annotated[list[AnyMessage], add_messages]
    user_info: List[Dict[str, Any]]

class Assistant:
    def __init__(self, runnable: Runnable):
        self.runnable = runnable

    def __call__(self, state: State, config: RunnableConfig):
        # Let the LLM handle all requests directly
        while True:
            result = self.runnable.invoke(state)
            if not result.tool_calls and (
                not result.content
                or isinstance(result.content, list)
                and not result.content[0].get("text")
            ):
                messages = state["messages"] + [("user", "Respond with a real output.")]
                state = {**state, "messages": messages}
            else:
                break
        return {"messages": result}

def getLLm():
    """Get LLM instance based on environment configuration"""
    use_ollama = os.getenv("USE_OLLAMA") == "true"
    temperature = float(os.getenv("LLM_TEMPERATURE", "0.2"))
    if use_ollama:
        return ChatOllama(model=os.getenv("LLM_MODEL", "llama2"), temperature=temperature)
    else:
        return ChatGoogleGenerativeAI(model=os.getenv("LLM_MODEL", "gemini-pro"), temperature=temperature)

# Define tool groups
safe_tools = [

]

sensitive_tools = [
    add_to_cart,
    update_cart_item,
    place_order,
    cancel_order,
    clear_cart,
    fetch_user_order_information,
    lookup_store_policy,
    view_cart,
    semantic_product_search,
    get_product_cultural_context,
    get_similar_products
]

# Remove the module-level LLM instantiation and assistant_runnable
# These should be created by the EnhancedChatBot class to ensure consistency