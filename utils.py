from langchain_core.messages import ToolMessage, AIMessage, HumanMessage
from langchain_core.runnables import RunnableLambda
from langgraph.prebuilt import ToolNode
import json
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

def debug_log(message, data=None, level="INFO"):
    """Enhanced logging with timestamp and formatting"""
    timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
    
    if level == "ERROR":
        color = "\033[91m"  # Red
    elif level == "WARN":
        color = "\033[93m"   # Yellow
    elif level == "SUCCESS":
        color = "\033[92m"   # Green
    else:
        color = "\033[94m"   # Blue
    
    reset = "\033[0m"
    
    print(f"{color}[{timestamp}] {level}: {message}{reset}")
    
    if data is not None:
        if isinstance(data, (dict, list)):
            try:
                print(f"  Data: {json.dumps(data, indent=2, ensure_ascii=False)}")
            except Exception as e:
                print(f"  Data (raw): {data}")
        else:
            print(f"  Data: {data}")

def log_message(message, prefix="MSG"):
    """Log message content with type detection"""
    if isinstance(message, AIMessage):
        debug_log(f"{prefix} AI Message", {
            "content": message.content[:200] if message.content else "No content",
            "tool_calls": len(message.tool_calls) if message.tool_calls else 0,
            "tool_calls_detail": message.tool_calls if message.tool_calls else None
        })
    elif isinstance(message, HumanMessage):
        debug_log(f"{prefix} Human Message", {
            "content": message.content[:200] if message.content else "No content"
        })
    elif isinstance(message, ToolMessage):
        debug_log(f"{prefix} Tool Message", {
            "content": message.content[:200] if message.content else "No content",
            "tool_call_id": getattr(message, 'tool_call_id', 'Unknown'),
            "name": getattr(message, 'name', 'Unknown')
        })
    else:
        debug_log(f"{prefix} Unknown Message Type", {
            "type": type(message).__name__,
            "content": str(message)[:200]
        })

def log_state(state, step_name="UNKNOWN"):
    """Log complete state information"""
    debug_log(f"=== STATE at {step_name} ===")
    
    if "messages" in state:
        debug_log(f"Messages count: {len(state['messages'])}")
        for i, msg in enumerate(state.get("messages", [])[-3:]):  # Last 3 messages
            log_message(msg, f"MSG[{i}]")
    
    if "user_info" in state:
        debug_log(f"User info: {state.get('user_info', [])}")
    
    if "selections" in state:
        debug_log(f"Selections: {state.get('selections', [])}")
    
    debug_log("=== END STATE ===")

def handle_tool_error(state) -> dict:
    """Enhanced tool error handling with detailed logging"""
    error = state.get("error")
    tool_calls = state["messages"][-1].tool_calls
    
    debug_log("TOOL ERROR occurred", {
        "error": str(error),
        "tool_calls": tool_calls
    }, "ERROR")
    
    return {
        "messages": [
            ToolMessage(
                content=f"Error: {repr(error)}\n please fix your mistakes.",
                tool_call_id=tc["id"],
            )
            for tc in tool_calls
        ]
    }

def create_tool_node_with_fallback(tools: list) -> dict:
    """Create tool node with enhanced error handling and logging"""
    def log_before_tools(state):
        debug_log("=== BEFORE TOOL EXECUTION ===")
        log_state(state, "TOOL_INPUT")
        
        # Log tool calls details
        if state.get("messages") and state["messages"][-1].tool_calls:
            for i, tool_call in enumerate(state["messages"][-1].tool_calls):
                debug_log(f"Tool Call {i+1}", {
                    "name": tool_call.get("name"),
                    "args": tool_call.get("args"),
                    "id": tool_call.get("id")
                })
        return state
    
    def log_after_tools(state):
        debug_log("=== AFTER TOOL EXECUTION ===")
        log_state(state, "TOOL_OUTPUT")
        return state
    
    # Create the tool node with logging
    base_node = ToolNode(tools)
    
    # Wrap with logging
    logged_node = (
        RunnableLambda(log_before_tools) | 
        base_node | 
        RunnableLambda(log_after_tools)
    )
    
    return logged_node.with_fallbacks(
        [RunnableLambda(handle_tool_error)], exception_key="error"
    )

def clean_deepseek_response(content: str) -> str:
    """Clean Deepseek model response from tool artifacts"""
    if not content:
        return content
        
    # Remove tool output markers
    markers_to_remove = [
        "<｜tool ▁outputs ▁begin｜>",
        "<｜tool ▁output ▁begin｜>",
        "<｜tool ▁output ▁end｜>", 
        "<｜tool ▁outputs ▁end｜>",
        "<｜thinking｜>",
        "<｜/thinking｜>"
    ]
    
    cleaned = content
    for marker in markers_to_remove:
        cleaned = cleaned.replace(marker, "")
    
    # Remove multiple newlines
    import re
    cleaned = re.sub(r'\n\s*\n', '\n\n', cleaned)
    cleaned = cleaned.strip()
    
    debug_log("Cleaned Deepseek response", {
        "original_length": len(content),
        "cleaned_length": len(cleaned),
        "had_markers": any(marker in content for marker in markers_to_remove)
    })
    
    return cleaned

def _print_event(event: dict, _printed: set, max_length=1500):
    current_state = event.get("dialog_state")
    if current_state:
        print("Currently in: ", current_state[-1])
    message = event.get("messages")
    if message:
        if isinstance(message, list):
            message = message[-1]
        if message.id not in _printed:
            msg_repr = message.pretty_repr(html=True)
            if len(msg_repr) > max_length:
                msg_repr = msg_repr[:max_length] + " ... (truncated)"
            print(msg_repr)
            _printed.add(message.id)