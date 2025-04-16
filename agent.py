from typing import Annotated, Dict, Any, List
from datetime import datetime
from typing_extensions import TypedDict

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

class State(TypedDict):
    messages: Annotated[list[AnyMessage], add_messages]
    user_info: List[Dict[str, Any]]

class Assistant:
    def __init__(self, runnable: Runnable):
        self.runnable = runnable

    def __call__(self, state: State, config: RunnableConfig):
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

llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash", temperature=0.7)

assistant_prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "You are a friendly customer support assistant for a handicraft store. "
            "Respond in Vietnamese if the user speaks Vietnamese, otherwise use English. "
            "Use tools to search products, check orders, manage cart, or assist with policies. "
            "When searching products, use categories ('Nón', 'Giỏ', 'Đồ Gia Dụng', 'Tranh', 'Tượng') "
            "and materials ('Lá cọ', 'Tre', 'Gỗ', 'Vải', 'Mây', 'Đá'). "
            "For vague requests (e.g., 'something', 'mua 10 cái'), clarify by asking about "
            "category (e.g., 'Nón hay Tượng?'), material (e.g., 'Gỗ hay Tre?'), price range (e.g., 'Dưới 500k?'), "
            "or quantity (e.g., 'Cụ thể bao nhiêu cái?'). "
            "For 'đắt nhất' or 'most expensive', use search_products with sort_by_price='desc'. "
            "For 'rẻ nhất' or 'cheapest', use sort_by_price='asc'. "
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