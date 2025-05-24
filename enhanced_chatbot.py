from typing import Annotated, Dict, Any, List, Optional
from typing_extensions import TypedDict
from datetime import datetime
from langgraph.graph import END, StateGraph, START
from langgraph.prebuilt import tools_condition
from langgraph.checkpoint.memory import MemorySaver
from langchain_core.messages import ToolMessage, AIMessage
from langchain_core.runnables import RunnableConfig
from langchain_core.prompts import ChatPromptTemplate
from langgraph.graph.message import add_messages, AnyMessage
import logging

from agent import getLLm, safe_tools, sensitive_tools
from tools import fetch_user_order_information
from constants import CATEGORIES, MATERIALS
from utils import create_tool_node_with_fallback

logger = logging.getLogger(__name__)

# Enhanced State that includes thinking
class ThinkingState(TypedDict):
    messages: Annotated[list[AnyMessage], add_messages]
    user_info: List[Dict[str, Any]]
    selections: Optional[List[Dict[str, str]]]
    pending_approval: Optional[Dict[str, Any]]
    next_action: Optional[str]

class EnhancedChatBot:
    def __init__(self, customer_id="CUST001"):
        self.memory = MemorySaver()
        self.llm = getLLm()
        self.config = {
            "configurable": {
                "customer_id": customer_id,
                "thread_id": f"thread_{customer_id}"
            }
        }
        
        # Build category strings once
        self.categories_str = ", ".join([f"'{cat}'" for cat in CATEGORIES])
        self.materials_str = ", ".join([f"'{mat}'" for mat in MATERIALS])
        
        self.graph = self._build_graph()

    def _build_graph(self):
        """Build the LangGraph with proper approval handling like the first implementation"""
        builder = StateGraph(ThinkingState)

        # 1. Initialize - Fetch customer info
        def fetch_customer_info(state: ThinkingState, config: RunnableConfig):
            try:
                user_info = fetch_user_order_information.invoke({}, config)
                return {"user_info": user_info}
            except Exception as e:
                logger.error(f"Error fetching customer info: {str(e)}")
                return {"user_info": []}

        # 2. Assistant - Main response generation
        def assistant(state: ThinkingState, config: RunnableConfig):
            """Main assistant node with full context"""
            assistant_prompt = ChatPromptTemplate.from_messages([
                ("system",
                 "You are a friendly customer support assistant for a Vietnamese handicraft store. "
                 "Respond in Vietnamese if the user speaks Vietnamese, otherwise use English. "
                 f"Store categories: {self.categories_str}. "
                 f"Store materials: {self.materials_str}. "
                 "\n\nGuidelines:"
                 "\n- Check stock before adding to cart"
                 "\n- Suggest alternatives if out of stock"
                 "\n- Keep responses helpful and concise"
                 "\nCustomer info: {user_info}"
                 "\nCurrent time: {time}"
                ),
                ("placeholder", "{messages}")
            ]).partial(time=str(datetime.now()))
            
            chain = assistant_prompt | self.llm.bind_tools(safe_tools + sensitive_tools)
            result = chain.invoke({
                "messages": state["messages"],
                "user_info": state.get("user_info", [])
            })
            
            return {"messages": [result]}

        # 3. Generate selections based on conversation context
        def generate_selections(state: ThinkingState, config: RunnableConfig):
            """Generate follow-up options based on the conversation"""
            if not state["messages"]:
                return {"selections": self._default_selections()}
            
            # Get the last assistant message
            last_assistant_msg = None
            for msg in reversed(state["messages"]):
                if isinstance(msg, AIMessage):
                    last_assistant_msg = msg.content
                    break
            
            if not last_assistant_msg:
                return {"selections": self._default_selections()}

            try:
                selection_prompt = ChatPromptTemplate.from_messages([
                    ("system",
                     "Generate 2-4 helpful follow-up options for the user based on the conversation. "
                     "Format as short phrases (3-5 words). Use Vietnamese unless user speaks English. "
                     "If possible, try to aim for sales, always try to sell the product. "
                     f"Categories: {self.categories_str}. Materials: {self.materials_str}. "
                     "Return each option on a new line, no numbering or bullets."
                    ),
                    ("human", "Assistant response: {response}")
                ])
                
                chain = selection_prompt | self.llm
                result = chain.invoke({
                    "response": last_assistant_msg
                })
                
                # Parse options
                options = []
                for line in result.content.split('\n'):
                    line = line.strip()
                    if line and not line.startswith(('Here', 'Option', 'Follow')):
                        clean_option = line.strip('•-*"\'0123456789. ')
                        if clean_option:
                            options.append({"text": clean_option, "value": clean_option})
                
                return {"selections": options if options else self._default_selections()}
            except Exception as e:
                logger.error(f"Error generating selections: {str(e)}")
                return {"selections": self._default_selections()}

        # 4. Handle tool routing (same as first implementation)
        def route_tools(state: ThinkingState):
            """Route to appropriate tool node based on tool sensitivity"""
            next_node = tools_condition(state)
            if next_node == END:
                return "generate_selections"
            
            ai_message = state["messages"][-1]
            if not ai_message.tool_calls:
                return "generate_selections"
            
            first_tool_call = ai_message.tool_calls[0]
            sensitive_tool_names = {t.name for t in sensitive_tools}
            
            if first_tool_call["name"] in sensitive_tool_names:
                return "sensitive_tools"
            return "safe_tools"

        # Add all nodes
        builder.add_node("fetch_user_info", fetch_customer_info)
        builder.add_node("assistant", assistant)
        builder.add_node("safe_tools", create_tool_node_with_fallback(safe_tools))
        builder.add_node("sensitive_tools", create_tool_node_with_fallback(sensitive_tools))
        builder.add_node("generate_selections", generate_selections)

        # Define the flow - CRITICAL: Same structure as working first implementation
        builder.add_edge(START, "fetch_user_info")
        builder.add_edge("fetch_user_info", "assistant")
        
        # Route from assistant to tools or selections
        builder.add_conditional_edges(
            "assistant", 
            route_tools, 
            ["safe_tools", "sensitive_tools", "generate_selections"]
        )
        
        # Safe tools go back to assistant, then generate selections
        builder.add_edge("safe_tools", "assistant")
        
        # Sensitive tools go back to assistant, then generate selections
        builder.add_edge("sensitive_tools", "assistant")
        
        # Selections end the flow
        builder.add_edge("generate_selections", END)

        # CRITICAL: Use same interrupt pattern as first implementation
        return builder.compile(
            checkpointer=self.memory,
            interrupt_before=["sensitive_tools"]
        )

    def _default_selections(self):
        """Default selection options"""
        return [
            {"text": "Xem sản phẩm", "value": "Xem sản phẩm"},
            {"text": "Xem giỏ hàng", "value": "Xem giỏ hàng"},
            {"text": "Chính sách", "value": "Chính sách"}
        ]

    def invoke(self, question: str, verbose: bool = False) -> Dict[str, Any]:
        """
        Invoke the chatbot - simplified like the first implementation
        """
        if verbose:
            print(f"\nUser: {question}")

        # Stream through the graph
        events = self.graph.stream(
            {"messages": [("user", question)]},
            self.config,
            stream_mode="values"
        )
        
        final_state = None
        for event in events:
            final_state = event

        if not final_state:
            return {
                "response": "Không có phản hồi.",
                "status": "error",
                "selections": self._default_selections()
            }

        # Check if we're waiting for approval (same logic as first implementation)
        snapshot = self.graph.get_state(self.config)
        if snapshot.next and "sensitive_tools" in snapshot.next:
            # Extract the tool call for approval
            ai_message = final_state["messages"][-1]
            if not ai_message.tool_calls:
                return {
                    "response": "Không có hành động nhạy cảm.",
                    "status": "completed",
                    "selections": self._default_selections()
                }

            tool_call = ai_message.tool_calls[0]
            
            # Generate approval message based on tool
            response = self._generate_approval_message(tool_call)
            
            return {
                "response": response,
                "status": "waiting",
                "waiting_for_approval": True,
                "tool_call": tool_call,
                "selections": [
                    {"text": "Đồng ý", "value": "approve"},
                    {"text": "Từ chối", "value": "reject"}
                ]
            }

        # Normal completion - get response and generate selections
        last_message = final_state.get("messages", [])[-1] if final_state.get("messages") else None
        response = last_message.content if last_message and hasattr(last_message, "content") else "Không có phản hồi."
        
        # Generate selections for the response
        try:
            selections = self._generate_selections_for_response(response)
        except Exception as e:
            logger.error(f"Error generating selections: {str(e)}")
            selections = self._default_selections()

        return {
            "response": response,
            "status": "completed",
            "selections": selections
        }

    def _generate_approval_message(self, tool_call: Dict[str, Any]) -> str:
        """Generate approval message based on tool call"""
        try:
            tool_name = tool_call.get('name', 'unknown')
            tool_args = tool_call.get('args', {})
            
            if tool_name == "add_to_cart":
                product_id = tool_args.get('product_id', 'unknown')
                quantity = tool_args.get('quantity', 1)
                return f"Bạn có muốn thêm {quantity} sản phẩm (ID: {product_id}) vào giỏ hàng không?"
            elif tool_name == "update_cart_item":
                product_id = tool_args.get('product_id', 'unknown')
                quantity = tool_args.get('quantity', 1)
                return f"Bạn có muốn cập nhật số lượng sản phẩm (ID: {product_id}) thành {quantity} không?"
            elif tool_name == "place_order":
                return "Bạn có muốn đặt hàng với các sản phẩm trong giỏ hàng hiện tại không?"
            elif tool_name == "cancel_order":
                order_id = tool_args.get('order_id', 'unknown')
                return f"Bạn có muốn hủy đơn hàng #{order_id} không?"
            elif tool_name == "clear_cart":
                return "Bạn có muốn xóa tất cả sản phẩm trong giỏ hàng không?"
            elif tool_name == "view_cart":
                return "Bạn có muốn xem giỏ hàng hiện tại không?"
            else:
                return f"Cần xác nhận: {tool_name} với tham số {tool_args}"
        except Exception as e:
            logger.error(f"Error generating approval message: {str(e)}")
            return "Đang chờ xác nhận..."

    def handle_approval(self, approved: bool, message: Optional[str] = None) -> Dict[str, Any]:
        """Handle approval - simplified like the first implementation"""
        try:
            snapshot = self.graph.get_state(self.config)
            
            if not snapshot.next or "sensitive_tools" not in snapshot.next:
                return {
                    "response": "Không có hành động đang chờ xác nhận.",
                    "status": "completed",
                    "selections": self._default_selections()
                }

            # Get the tool call that needs approval
            current_state = snapshot.values
            ai_message = current_state["messages"][-1]
            
            if not ai_message.tool_calls:
                return {
                    "response": "Không thể tìm thấy hành động cần xác nhận.",
                    "status": "error",
                    "selections": self._default_selections()
                }

            tool_call = ai_message.tool_calls[0]

            if approved:
                # Continue the graph execution
                events = self.graph.stream(None, self.config, stream_mode="values")
                final_state = None
                for event in events:
                    final_state = event
                
                response = "Hành động đã được thực hiện."
                if final_state and final_state.get("messages"):
                    last_message = final_state["messages"][-1]
                    if hasattr(last_message, "content") and last_message.content:
                        response = last_message.content
                
                # Generate selections for the response
                try:
                    selections = self._generate_selections_for_response(response)
                except Exception as e:
                    logger.error(f"Error generating selections: {str(e)}")
                    selections = self._default_selections()
                
                return {
                    "response": response,
                    "status": "completed",
                    "selections": selections
                }
            else:
                # Handle rejection - same as first implementation
                reject_message = "Hành động bị từ chối bởi người dùng."
                if message:
                    reject_message += f" Lý do: {message}"
                
                tool_message = ToolMessage(
                    tool_call_id=tool_call["id"],
                    content=reject_message
                )
                
                # Update the graph with the rejection
                self.graph.update_state(
                    self.config,
                    {"messages": [tool_message]}
                )
                
                # Continue execution after rejection
                events = self.graph.stream(None, self.config, stream_mode="values")
                final_state = None
                for event in events:
                    final_state = event
                    
                response = "Hành động đã bị từ chối. Vui lòng cho biết bạn muốn làm gì tiếp theo."
                if final_state and final_state.get("messages"):
                    last_message = final_state["messages"][-1]
                    if hasattr(last_message, "content") and last_message.content:
                        response = last_message.content
                
                return {
                    "response": response,
                    "status": "completed",
                    "selections": self._default_selections()
                }
                
        except Exception as e:
            logger.error(f"Error in handle_approval: {str(e)}", exc_info=True)
            return {
                "response": f"Đã xảy ra lỗi khi xử lý xác nhận: {str(e)}",
                "status": "error",
                "selections": self._default_selections()
            }

    def _generate_selections_for_response(self, response: str) -> List[Dict[str, str]]:
        """Generate selections based on a response"""
        try:
            selection_prompt = ChatPromptTemplate.from_messages([
                ("system",
                 "Generate 2-4 helpful follow-up options for the user based on the conversation. "
                 "Format as short phrases (3-5 words). Use Vietnamese unless user speaks English. "
                 "If possible, try to aim for sales, always try to sell the product. "
                 f"Categories: {self.categories_str}. Materials: {self.materials_str}. "
                 "Return each option on a new line, no numbering or bullets."
                ),
                ("human", "Assistant response: {response}")
            ])
            
            chain = selection_prompt | self.llm
            result = chain.invoke({
                "response": response
            })
            
            # Parse options
            options = []
            for line in result.content.split('\n'):
                line = line.strip()
                if line and not line.startswith(('Here', 'Option', 'Follow')):
                    clean_option = line.strip('•-*"\'0123456789. ')
                    if clean_option:
                        options.append({"text": clean_option, "value": clean_option})
            
            return options if options else self._default_selections()
        except Exception as e:
            logger.error(f"Error generating selections: {str(e)}")
            return self._default_selections()
