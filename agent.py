from typing import Annotated, Dict, Any, List
from datetime import datetime
from typing_extensions import TypedDict
import os
from langchain_ollama import ChatOllama
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import Runnable, RunnableConfig
from langgraph.graph.message import add_messages, AnyMessage
from tools import (
    fetch_user_order_information,
    search_products,
    lookup_store_policy,
    view_cart,
    add_to_cart,
    update_cart_item,
    clear_cart,
    place_order,
    cancel_order
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
    use_ollama=os.getenv("USE_OLLAMA") == "true"
    temperature=float(os.getenv("LLM_TEMPERATURE"))
    if use_ollama:
        return ChatOllama(model=os.getenv("LLM_MODEL"), temperature=temperature)
    else:
        return ChatGoogleGenerativeAI(model=os.getenv("LLM_MODEL"), temperature=temperature)

llm = getLLm()

assistant_prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "You are a friendly customer support assistant for a handicraft store. "
            "Respond in Vietnamese if the user speaks Vietnamese, otherwise use English. "
            "Use tools to search products, check orders, place order, manage cart, or assist with policies. "
            "Always check stock_quantity with search_products before calling add_to_cart or place_order. "
            "If stock is insufficient, suggest alternatives (e.g., 'Chỉ còn 5 Nón, muốn xem Giỏ không?'). "
            "If no products match, explain (e.g., 'Không tìm thấy Tượng Gỗ, thử Tranh nhé?'). "
            "For invalid inputs (e.g., 'mua 9999 cái'), inform the user politely (e.g., 'Số lượng lớn quá, kho chỉ có...'). "
            "If a tool fails, apologize and offer to retry or clarify. "
            "For cart management, use add_to_cart, update_cart_item, view_cart, clear_cart, and confirm before place_order. "
            "Show cart status when relevant using view_cart (Người dùng yêu cầu xem giỏ hàng). "
            "Keep responses concise, warm, and helpful. "
            "\n\nCurrent customer order history:\n<Customer>\n{user_info}\n</Customer>"
            "Current time: {time}."
        ),
        ("placeholder", "{messages}"),
    ]
).partial(time=str(datetime.now()))


safe_tools = [
    fetch_user_order_information,
    search_products,
    lookup_store_policy,
    view_cart
]

sensitive_tools = [
    add_to_cart,
    update_cart_item,
    place_order,
    cancel_order,
    clear_cart
]

assistant_runnable = assistant_prompt | llm.bind_tools(safe_tools + sensitive_tools)