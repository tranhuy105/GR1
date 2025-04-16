from typing import Dict, Any, Optional, Callable
from langgraph.graph import END, StateGraph, START
from langgraph.prebuilt import tools_condition
from langgraph.checkpoint.memory import MemorySaver
from langchain_core.messages import ToolMessage
from langchain_core.runnables import RunnableConfig

from agent import State, Assistant, assistant_runnable, safe_tools, sensitive_tools
from utils import create_tool_node_with_fallback, _print_event
from tools import fetch_user_order_information
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

class ChatBot:
    def __init__(self):
        self.memory = MemorySaver()
        self.graph = self._build_graph()
        self.config = {
            "configurable": {
                "customer_id": "CUST001",
                "thread_id": "test_thread"
            }
        }
        self._printed = set()  # For _print_event

    def _build_graph(self):
        builder = StateGraph(State)

        def fetch_customer_info(state: State, config: RunnableConfig):
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

        return builder.compile(checkpointer=self.memory, interrupt_before=["sensitive_tools"])

    def invoke(
        self,
        question: str,
        confirm_callback: Optional[Callable[[Dict[str, Any]], bool]] = None,
        verbose: bool = False
    ) -> Dict[str, Any]:
        """
        Invoke the chatbot with a question.
        Args:
            question: User input question.
            confirm_callback: Optional function to handle sensitive tool confirmation.
                              Takes tool_call dict, returns True to proceed, False to reject.
            verbose: If True, print detailed events like original graph.py.
        Returns:
            Dict with 'response' (final answer) and 'status' (completed/waiting).
        """
        if verbose:
            print(f"\nUser: {question}")
            self._printed.clear()  # Reset printed messages

        events = self.graph.stream(
            {"messages": [("user", question)], "user_info": []},
            self.config,
            stream_mode="values"
        )
        last_event = None
        for event in events:
            if verbose:
                _print_event(event, self._printed)
            last_event = event

        if not last_event or "messages" not in last_event:
            response = "Không có phản hồi."
            if verbose:
                print(f"\nAssistant: {response}")
            return {"response": response, "status": "completed"}

        snapshot = self.graph.get_state(self.config)
        if not snapshot.next:
            last_message = last_event["messages"][-1]
            response = last_message.content if hasattr(last_message, "content") else str(last_message)
            if verbose:
                print(f"\nAssistant: {response}")
            return {"response": response, "status": "completed"}

        # Handle sensitive tool interrupt
        ai_message = last_event["messages"][-1]
        if not ai_message.tool_calls:
            response = "Không có hành động nhạy cảm."
            if verbose:
                print(f"\nAssistant: {response}")
            return {"response": response, "status": "completed"}

        tool_call = ai_message.tool_calls[0]
        if confirm_callback:
            approved = confirm_callback(tool_call)
        else:
            if verbose:
                print(f"Tool Call: {tool_call}")
            user_input = input("Bạn có đồng ý với hành động trên không? Gõ 'y' để tiếp tục: ")
            approved = user_input.strip().lower() == "y"

        if approved:
            result = self.graph.invoke(None, self.config)
            events = self.graph.stream(None, self.config, stream_mode="values")
            last_event = None
            for event in events:
                if verbose:
                    _print_event(event, self._printed)
                last_event = event
            last_message = last_event["messages"][-1]
            response = last_message.content if hasattr(last_message, "content") else str(last_message)
            if verbose:
                print(f"\nAssistant: {response}")
            return {"response": response, "status": "completed"}
        else:
            reject_message = ToolMessage(
                tool_call_id=tool_call["id"],
                content="Hành động bị từ chối bởi người dùng."
            )
            self.graph.invoke({"messages": [reject_message]}, self.config)
            response = "Hành động bị từ chối. Vui lòng thử lại."
            if verbose:
                print(f"\nAssistant: {response}")
            return {"response": response, "status": "completed"}

if __name__ == "__main__":
    from db_setup_fixed import setup_database
    setup_database(clear_existing=True)

    bot = ChatBot()
    print("Chào bạn! Hãy nhập câu hỏi (gõ 'exit' để thoát):")

    while True:
        question = input("\nYou: ")
        if question.lower().strip() == "exit":
            print("Tạm biệt!")
            break

        result = bot.invoke(question, verbose=True)
        if not result["response"].startswith("Assistant:"):
            print(f"\nAssistant: {result['response']}")