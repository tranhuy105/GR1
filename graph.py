from langgraph.graph import END, StateGraph, START
from langgraph.prebuilt import tools_condition
from langgraph.checkpoint.memory import MemorySaver
from langchain_core.messages import ToolMessage
from langchain_core.runnables import RunnableConfig

from agent import State, Assistant, assistant_runnable, safe_tools, sensitive_tools
from utils import create_tool_node_with_fallback, _print_event
from tools import fetch_user_order_information
from db_setup import setup_database
import logging

logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger(__name__)

builder = StateGraph(State)

def fetch_customer_info(state: State, config: RunnableConfig):
    """Fetch customer information at the start of conversation."""
    try:
        user_info = fetch_user_order_information.invoke({}, config)
        return {"user_info": user_info}
    except Exception as e:
        logger.error(f"Error fetching customer info: {str(e)}")
        return {"user_info": []}

builder.add_node("fetch_user_info", fetch_customer_info)
builder.add_edge(START, "fetch_user_info")
builder.add_node("assistant", Assistant(assistant_runnable))
builder.add_node("safe_tools", create_tool_node_with_fallback(safe_tools))
builder.add_node("sensitive_tools", create_tool_node_with_fallback(sensitive_tools))
builder.add_edge("fetch_user_info", "assistant")

def route_tools(state: State):
    """Route tool calls to safe or sensitive nodes."""
    next_node = tools_condition(state)
    if next_node == END:
        return END
    ai_message = state["messages"][-1]
    first_tool_call = ai_message.tool_calls[0]
    sensitive_tool_names = {t.name for t in sensitive_tools}
    if first_tool_call["name"] in sensitive_tool_names:
        return "sensitive_tools"
    return "safe_tools"

builder.add_conditional_edges(
    "assistant", route_tools, ["safe_tools", "sensitive_tools", END]
)
builder.add_edge("safe_tools", "assistant")
builder.add_edge("sensitive_tools", "assistant")

memory = MemorySaver()
graph = builder.compile(
    checkpointer=memory,
    interrupt_before=["sensitive_tools"]
)

if __name__ == "__main__":
    # clear database before running
    setup_database(clear_existing=True)

    config = {
        "configurable": {
            "customer_id": "CUST001",
            "thread_id": "test_thread"
        }
    }
    
    _printed = set()
    print("Chào bạn! Hãy nhập câu hỏi (gõ 'exit' để thoát):")
    
    while True:
        try:
            question = input("\nYou: ")
            if question.lower().strip() == "exit":
                print("Tạm biệt!")
                break
            
            print(f"\nUser: {question}")
            events = graph.stream(
                {"messages": [("user", question)], "user_info": []},
                config,
                stream_mode="values"
            )
            for event in events:
                _print_event(event, _printed)
            snapshot = graph.get_state(config)
            
            while snapshot.next:
                try:
                    user_input = input(
                        "Bạn có đồng ý với hành động trên không? Gõ 'y' để tiếp tục; "
                        "hoặc giải thích lý do từ chối.\n\n"
                    )
                except KeyboardInterrupt:
                    print("\nExiting...")
                    break
                except:
                    user_input = "y"
                
                if user_input.strip() == "y":
                    result = graph.invoke(None, config)
                else:
                    if "messages" in event and event["messages"] and hasattr(event["messages"][-1], "tool_calls") and event["messages"][-1].tool_calls:
                        last_tool_call = event["messages"][-1].tool_calls[0]
                        result = graph.invoke(
                            {
                                "messages": [
                                    ToolMessage(
                                        tool_call_id=last_tool_call["id"],
                                        content=f"Hành động bị từ chối. Lý do: '{user_input}'. Vui lòng điều chỉnh và tiếp tục hỗ trợ."
                                    )
                                ]
                            },
                            config,
                        )
                    else:
                        result = graph.invoke(
                            {
                                "messages": [("user", f"Tôi không đồng ý: {user_input}. Vui lòng làm rõ hoặc điều chỉnh.")]
                            },
                            config,
                        )
                
                events = graph.stream(None, config, stream_mode="values")
                for event in events:
                    _print_event(event, _printed)
                snapshot = graph.get_state(config)
        except Exception as e:
            print(f"Lỗi khi xử lý câu hỏi: {str(e)}")
            continue