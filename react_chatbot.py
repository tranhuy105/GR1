from typing import Annotated, Dict, Any, List, Optional
from typing_extensions import TypedDict
from datetime import datetime
import os
from langgraph.graph import END, StateGraph, START
from langgraph.prebuilt import tools_condition
from langgraph.checkpoint.memory import MemorySaver
from langchain_core.messages import ToolMessage, AIMessage
from langchain_core.runnables import RunnableConfig
from langchain_core.prompts import ChatPromptTemplate
from langgraph.graph.message import add_messages, AnyMessage
import logging

from agent import getLLm, safe_tools, sensitive_tools
from constants import CATEGORIES, MATERIALS
from utils import create_tool_node_with_fallback, debug_log, log_state

logger = logging.getLogger(__name__)

# Enhanced State that includes thinking
class ReACTState(TypedDict):
    messages: Annotated[list[AnyMessage], add_messages]
    user_info: Dict[str, Any]
    thinking: Optional[str]  # Store the thinking process
    selections: Optional[List[Dict[str, str]]]
    pending_approval: Optional[Dict[str, Any]]
    next_action: Optional[str]

class ReACTChatBot:
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
        
        # Get environment variables for features
        self.use_llm_selections = self._parse_bool_env("USE_LLM_SELECTIONS", False)
        debug_log(f"Using LLM for selection generation: {self.use_llm_selections}")
        
        self.graph = self._build_graph()

    def _parse_bool_env(self, key: str, default: bool = False) -> bool:
        """Parse boolean environment variable safely"""
        value = os.getenv(key, str(default)).strip().lower()
        return value in ["1", "true", "yes", "on", "t"]

    def _build_graph(self):
        """Build the ReACT LangGraph with thinking step"""
        debug_log("=== BUILDING ReACT GRAPH ===")
        builder = StateGraph(ReACTState)

        # 1. Initialize - Return static customer info
        def fetch_customer_info(state: ReACTState, config: RunnableConfig):
            debug_log("Fetching static customer info")
            try:
                user_info = {
                    "customer_id": config["configurable"]["customer_id"],
                    "name": "Trần Quang Huy",
                    "phone": "+84 123 456 789",
                    "email": "imhuy105@example.com",
                    "address": "123 Le Loi Street, District 1, Ho Chi Minh City",
                    "membership_level": "Gold",
                    "registration_date": "2023-01-15",
                    "preferred_language": "Vietnamese",
                    "loyalty_points": 2500
                }
                debug_log("Static customer info created", user_info)
                return {"user_info": user_info}
            except Exception as e:
                debug_log(f"Error creating customer info: {str(e)}", level="ERROR")
                return {"user_info": {}}

        # 2. ANALYZE - Analyze the user's request and plan response
        def analyze_request(state: ReACTState, config: RunnableConfig):
            """ReACT Thinking step - analyze user request and plan response"""
            debug_log("=== ANALYZE NODE ENTRY ===")
            
            # Get the last user message
            user_message = None
            for msg in reversed(state["messages"]):
                if hasattr(msg, 'type') and msg.type == "human":
                    user_message = msg.content
                    break
            
            if not user_message:
                debug_log("No user message found for analysis")
                return {"thinking": "No user input to analyze"}
            
            thinking_prompt = ChatPromptTemplate.from_messages([
                ("system",
                 "You are analyzing a customer's request for a Vietnamese handicraft store. "
                 "Think step by step about what the customer wants and how to help them best.\n"
                 f"Store categories: {self.categories_str}\n"
                 f"Store materials: {self.materials_str}\n"
                 "Tools available: "
                    f"{', '.join([tool.name for tool in safe_tools + sensitive_tools])}\n\n"
                 "Customer info: {user_info}\n\n"
                 "THINKING PROCESS:\n"
                 "1. What is the customer asking for?\n"
                 "2. What information do I need to gather? (vague question should collect more data instead of calling tool - like product recommend)\n"
                 "3. What tools might I need to use?\n"
                 "4. What would be the most helpful response?\n"
                 "5. Are there any sales opportunities?\n\n"
                 "Respond with your thinking process in Vietnamese, be concise but thorough. Dont use markdown formatting.\n"
                ),
                ("human", "Customer request: {user_message}")
            ])
            
            try:
                chain = thinking_prompt | self.llm
                result = chain.invoke({
                    "user_message": user_message,
                    "user_info": state.get("user_info", {})
                })
                
                thinking_content = result.content
                debug_log("Analysis process completed", {
                    "thinking_preview": thinking_content if thinking_content else "No thinking"
                })
                
                return {"thinking": thinking_content}
            except Exception as e:
                debug_log(f"Error in analysis: {str(e)}", level="ERROR")
                return {"thinking": f"Lỗi trong quá trình suy nghĩ: {str(e)}"}

        # 3. ACTION - Main response generation based on thinking
        def action(state: ReACTState, config: RunnableConfig):
            """ReACT Action step - generate response based on thinking"""
            debug_log("=== ACTION NODE ENTRY ===")
            log_state(state, "ACTION_INPUT")
            
            action_prompt = ChatPromptTemplate.from_messages([
                ("system",
                 "You are a friendly customer support assistant for a Vietnamese handicraft store. "
                 "Respond in Vietnamese if the user speaks Vietnamese, otherwise use English. "
                 f"Store categories: {self.categories_str}. "
                 f"Store materials: {self.materials_str}. "
                 "\n\nYou have already thought about the customer's request: {thinking}"
                 "\n\nNow take ACTION based on your thinking:"
                 "\n- Use tools when necessary (view cart, add to cart, etc.)"
                 "\n- Provide helpful information"
                 "\n- Suggest products when appropriate"
                 "\n- Keep responses helpful and concise"
                 "\nCustomer info: {user_info}"
                 "\nCurrent time: {time}"
                ),
                ("placeholder", "{messages}")
            ]).partial(time=str(datetime.now()))
            
            debug_log("Binding tools to LLM for action")
            
            chain = action_prompt | self.llm.bind_tools(safe_tools + sensitive_tools)
            debug_log("Invoking LLM chain for action")
            
            result = chain.invoke({
                "messages": state["messages"],
                "thinking": state.get("thinking", "Không có suy nghĩ trước đó"),
                "user_info": state.get("user_info", {})
            })
            
            debug_log("Action result received", {
                "has_content": bool(result.content),
                "content_preview": result.content if result.content else "No content",
                "has_tool_calls": bool(result.tool_calls),
                "tool_calls_count": len(result.tool_calls) if result.tool_calls else 0
            })
            
            debug_log("=== ACTION NODE EXIT ===")
            return {"messages": [result]}

        # 4. Generate selections based on conversation context
        def generate_selections(state: ReACTState, config: RunnableConfig):
            """Generate follow-up options based on the conversation"""
            debug_log("=== GENERATE SELECTIONS NODE ===")
            
            # Skip LLM selection generation if disabled
            if not self.use_llm_selections:
                debug_log("Using default selections (LLM selection generation disabled)")
                return {"selections": self._default_selections()}
            
            if not state["messages"]:
                debug_log("No messages found, using default selections")
                return {"selections": self._default_selections()}
            
            # Get the last assistant message
            last_assistant_msg = None
            for msg in reversed(state["messages"]):
                if isinstance(msg, AIMessage):
                    last_assistant_msg = msg.content
                    break
            
            if not last_assistant_msg:
                debug_log("No assistant message found, using default selections")
                return {"selections": self._default_selections()}

            try:
                debug_log("Generating selections using LLM")
                selection_prompt = ChatPromptTemplate.from_messages([
                    ("system",
                     "Generate 2-4 helpful follow-up options for the user based on the conversation. "
                     "Format as short phrases (3-5 words). Use Vietnamese unless user speaks English. "
                     "Consider the thinking process: {thinking} "
                     "If possible, try to aim for sales, always try to sell the product. "
                     f"Categories: {self.categories_str}. Materials: {self.materials_str}. "
                     "Return each option on a new line, no numbering or bullets."
                    ),
                    ("human", "Assistant response: {response}")
                ])
                
                chain = selection_prompt | self.llm
                result = chain.invoke({
                    "response": last_assistant_msg,
                    "thinking": state.get("thinking", "")
                })
                
                debug_log("LLM selection result", {
                    "content": result.content
                })
                
                # Parse options
                options = []
                for line in result.content.split('\n'):
                    line = line.strip()
                    if line and not line.startswith(('Here', 'Option', 'Follow')):
                        clean_option = line.strip('•-*"\'0123456789. ')
                        if clean_option:
                            options.append({"text": clean_option, "value": clean_option})
                
                debug_log(f"Generated {len(options)} options")
                return {"selections": options if options else self._default_selections()}
            except Exception as e:
                debug_log(f"Error generating selections: {str(e)}", level="ERROR")
                return {"selections": self._default_selections()}

        # 5. Handle tool routing with enhanced debugging
        def route_tools(state: ReACTState):
            """Route to appropriate tool node based on tool sensitivity"""
            debug_log("=== ROUTING TOOLS ===")
            
            next_node = tools_condition(state)
            if next_node == END:
                debug_log("No tool call detected, routing to generate_selections")
                return "generate_selections"
            
            if not state["messages"] or not hasattr(state["messages"][-1], "tool_calls"):
                debug_log("No tool calls in last message, routing to generate_selections")
                return "generate_selections"
            
            ai_message = state["messages"][-1]
            if not ai_message.tool_calls:
                debug_log("Empty tool_calls list, routing to generate_selections")
                return "generate_selections"
            
            first_tool_call = ai_message.tool_calls[0]
            sensitive_tool_names = {t.name for t in sensitive_tools}
            
            tool_name = first_tool_call.get("name", "unknown")
            
            if tool_name in sensitive_tool_names:
                debug_log(f"Routing sensitive tool: {tool_name} to sensitive_tools node")
                return "sensitive_tools"
            
            debug_log(f"Routing safe tool: {tool_name} to safe_tools node")
            return "safe_tools"

        # Add all nodes
        builder.add_node("fetch_user_info", fetch_customer_info)
        builder.add_node("analyze_request", analyze_request)  # NEW: Analysis step
        builder.add_node("action", action)                    # Renamed from "assistant"
        builder.add_node("safe_tools", create_tool_node_with_fallback(safe_tools))
        builder.add_node("sensitive_tools", create_tool_node_with_fallback(sensitive_tools))
        builder.add_node("generate_selections", generate_selections)

        # Define the ReACT flow: Analyze -> Act -> Use Tools (if needed) -> Generate Selections
        builder.add_edge(START, "fetch_user_info")
        builder.add_edge("fetch_user_info", "analyze_request")  # NEW: Always analyze first
        builder.add_edge("analyze_request", "action")           # Then act based on analysis
        
        # Route from action to tools or selections
        builder.add_conditional_edges(
            "action", 
            route_tools, 
            ["safe_tools", "sensitive_tools", "generate_selections"]
        )
        
        # Safe tools go back to action for final response, then generate selections
        builder.add_edge("safe_tools", "action")
        
        # Sensitive tools go back to action for final response, then generate selections
        builder.add_edge("sensitive_tools", "action")
        
        # Selections end the flow
        builder.add_edge("generate_selections", END)

        debug_log("ReACT Graph built successfully")
        
        return builder.compile(
            checkpointer=self.memory,
            interrupt_before=["sensitive_tools"]
        )

    def _default_selections(self):
        """Default selection options"""
        return [
            {"text": "Tôi muốn xem sản phẩm", "value": "Tôi muốn xem sản phẩm"},
            {"text": "Tôi muốn xem giỏ hàng", "value": "Tôi muốn xem giỏ hàng"},
            {"text": "Tôi muốn xem chính sách", "value": "Tôi muốn xem chính sách"}
        ]

    def invoke(self, question: str, verbose: bool = False) -> Dict[str, Any]:
        """
        Invoke the ReACT chatbot with enhanced debugging
        """
        debug_log("=== INVOKE ReACT CHATBOT ===")
        debug_log(f"User question: {question}")
        
        if verbose:
            print(f"\nUser: {question}")

        # Stream through the graph with event logging
        debug_log("Streaming through ReACT graph")
        events = self.graph.stream(
            {"messages": [("user", question)]},
            self.config,
            stream_mode="values"
        )
        
        final_state = None
        event_count = 0
        for event in events:
            event_count += 1
            debug_log(f"Event {event_count} received")
            if verbose and event.get("thinking"):
                print(f"💭 Analysis: {event['thinking']}")
            final_state = event

        debug_log(f"Stream complete, processed {event_count} events")
        if not final_state:
            debug_log("No final state returned", level="ERROR")
            return {
                "response": "Không có phản hồi.",
                "status": "error",
                "selections": self._default_selections(),
                "thinking": None
            }

        # Check if we're waiting for approval
        debug_log("Checking for approval state")
        snapshot = self.graph.get_state(self.config)
        if snapshot.next and "sensitive_tools" in snapshot.next:
            debug_log("Sensitive tool detected, awaiting approval")
            
            # Extract the tool call for approval
            ai_message = final_state["messages"][-1]
            if not ai_message.tool_calls:
                debug_log("No tool calls found in AI message", level="WARN")
                return {
                    "response": "Không có hành động nhạy cảm.",
                    "status": "completed",
                    "selections": self._default_selections(),
                    "thinking": final_state.get("thinking")
                }

            tool_call = ai_message.tool_calls[0]
            debug_log("Tool awaiting approval", {
                "tool_name": tool_call.get("name", "unknown"),
                "tool_args": tool_call.get("args", {})
            })
            
            # Generate approval message based on tool
            response = self._generate_approval_message(tool_call)
            
            return {
                "response": response,
                "status": "waiting",
                "waiting_for_approval": True,
                "tool_call": tool_call,
                "thinking": final_state.get("thinking"),
                "selections": [
                    {"text": "Đồng ý", "value": "approve"},
                    {"text": "Từ chối", "value": "reject"}
                ]
            }

        # Normal completion - get response and generate selections
        debug_log("Processing normal completion")
        last_message = final_state.get("messages", [])[-1] if final_state.get("messages") else None
        response = last_message.content if last_message and hasattr(last_message, "content") else "Không có phản hồi."
        
        # Generate selections for the response
        if self.use_llm_selections:
            debug_log("Generating selections for response")
            try:
                selections = self._generate_selections_for_response(response, final_state.get("thinking"))
            except Exception as e:
                debug_log(f"Error generating selections: {str(e)}", level="ERROR")
                selections = self._default_selections()
        else:
            debug_log("Using default selections (LLM selections disabled)")
            selections = self._default_selections()

        return {
            "response": response,
            "status": "completed",
            "selections": selections,
            "thinking": final_state.get("thinking")  # Return thinking for debugging
        }

    def _generate_approval_message(self, tool_call: Dict[str, Any]) -> str:
        """Generate approval message based on tool call"""
        debug_log("Generating approval message for tool")
        try:
            tool_name = tool_call.get('name', 'unknown')
            tool_args = tool_call.get('args', {})
            
            debug_log(f"Tool requiring approval: {tool_name}", tool_args)
            
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
            debug_log(f"Error generating approval message: {str(e)}", level="ERROR")
            return "Đang chờ xác nhận..."

    def handle_approval(self, approved: bool, message: Optional[str] = None) -> Dict[str, Any]:
        """Handle approval with enhanced debugging"""
        debug_log(f"=== HANDLE APPROVAL === (approved: {approved})")
        
        try:
            snapshot = self.graph.get_state(self.config)
            
            if not snapshot.next or "sensitive_tools" not in snapshot.next:
                debug_log("No sensitive tool waiting for approval", level="WARN")
                return {
                    "response": "Không có hành động đang chờ xác nhận.",
                    "status": "completed",
                    "selections": self._default_selections(),
                    "thinking": None
                }

            # Get the tool call that needs approval
            current_state = snapshot.values
            ai_message = current_state["messages"][-1]
            
            if not ai_message.tool_calls:
                debug_log("No tool calls found in message needing approval", level="ERROR")
                return {
                    "response": "Không thể tìm thấy hành động cần xác nhận.",
                    "status": "error",
                    "selections": self._default_selections(),
                    "thinking": current_state.get("thinking")
                }

            tool_call = ai_message.tool_calls[0]
            debug_log("Found tool call awaiting approval", {
                "name": tool_call.get("name"),
                "args": tool_call.get("args")
            })

            if approved:
                debug_log("Tool approved, continuing execution")
                # Continue the graph execution
                events = self.graph.stream(None, self.config, stream_mode="values")
                final_state = None
                event_count = 0
                for event in events:
                    event_count += 1
                    debug_log(f"Post-approval event {event_count}")
                    final_state = event
                
                debug_log(f"Approval stream complete, processed {event_count} events")
                
                response = "Hành động đã được thực hiện."
                if final_state and final_state.get("messages"):
                    last_message = final_state["messages"][-1]
                    if hasattr(last_message, "content") and last_message.content:
                        response = last_message.content
                
                # Generate selections for the response
                if self.use_llm_selections:
                    debug_log("Generating selections for post-approval response")
                    try:
                        selections = self._generate_selections_for_response(response, final_state.get("thinking"))
                    except Exception as e:
                        debug_log(f"Error generating selections: {str(e)}", level="ERROR")
                        selections = self._default_selections()
                else:
                    debug_log("Using default selections (LLM selections disabled)")
                    selections = self._default_selections()
                
                return {
                    "response": response,
                    "status": "completed",
                    "selections": selections,
                    "thinking": final_state.get("thinking")
                }
            else:
                debug_log("Tool rejected, handling rejection")
                # Handle rejection
                reject_message = "Hành động bị từ chối bởi người dùng."
                if message:
                    reject_message += f" Lý do: {message}"
                
                debug_log(f"Rejection message: {reject_message}")
                
                tool_message = ToolMessage(
                    tool_call_id=tool_call["id"],
                    content=reject_message
                )
                
                # Update the graph with the rejection
                debug_log("Updating graph state with rejection message")
                self.graph.update_state(
                    self.config,
                    {"messages": [tool_message]}
                )
                
                # Continue execution after rejection
                debug_log("Continuing execution after rejection")
                events = self.graph.stream(None, self.config, stream_mode="values")
                final_state = None
                event_count = 0
                for event in events:
                    event_count += 1
                    debug_log(f"Post-rejection event {event_count}")
                    final_state = event
                
                debug_log(f"Rejection stream complete, processed {event_count} events")
                    
                response = "Hành động đã bị từ chối. Vui lòng cho biết bạn muốn làm gì tiếp theo."
                if final_state and final_state.get("messages"):
                    last_message = final_state["messages"][-1]
                    if hasattr(last_message, "content") and last_message.content:
                        response = last_message.content
                
                return {
                    "response": response,
                    "status": "completed",
                    "selections": self._default_selections(),
                    "thinking": final_state.get("thinking")
                }
                
        except Exception as e:
            debug_log(f"Error in handle_approval: {str(e)}", level="ERROR")
            logger.error(f"Error in handle_approval: {str(e)}", exc_info=True)
            return {
                "response": f"Đã xảy ra lỗi khi xử lý xác nhận: {str(e)}",
                "status": "error",
                "selections": self._default_selections(),
                "thinking": None
            }

    def _generate_selections_for_response(self, response: str, thinking: Optional[str] = None) -> List[Dict[str, str]]:
        """Generate selections based on a response and thinking"""
        debug_log("Generating selections from response and thinking")
        
        if not self.use_llm_selections:
            debug_log("LLM selections disabled, returning defaults")
            return self._default_selections()
            
        try:
            selection_prompt = ChatPromptTemplate.from_messages([
                ("system",
                 "Generate 2-3 helpful follow-up options for the user based on the conversation. "
                 "Format as short phrases (3-5 words). Use Vietnamese unless user speaks English. "
                 "Consider the thinking process: {thinking} "
                 "If possible, try to aim for sales, always try to sell the product. "
                 f"Categories: {self.categories_str}. Materials: {self.materials_str}. "
                 "Return each option on a new line, no numbering or bullets."
                ),
                ("human", "Assistant response: {response}")
            ])
            
            chain = selection_prompt | self.llm
            result = chain.invoke({
                "response": response,
                "thinking": thinking or "Không có thông tin suy nghĩ"
            })
            
            debug_log("LLM selection result received", {
                "content": result.content[:100] if result.content else "None"
            })
            
            # Parse options
            options = []
            for line in result.content.split('\n'):
                line = line.strip()
                if line and not line.startswith(('Here', 'Option', 'Follow')):
                    clean_option = line.strip('•-*"\'0123456789. ')
                    if clean_option:
                        options.append({"text": clean_option, "value": clean_option})
            
            debug_log(f"Generated {len(options)} options")
            return options if options else self._default_selections()
        except Exception as e:
            debug_log(f"Error generating selections: {str(e)}", level="ERROR")
            logger.error(f"Error generating selections: {str(e)}")
            return self._default_selections()

    def get_thinking_process(self) -> Optional[str]:
        """Get the last thinking process for debugging"""
        try:
            snapshot = self.graph.get_state(self.config)
            return snapshot.values.get("thinking") if snapshot.values else None
        except Exception as e:
            debug_log(f"Error getting thinking process: {str(e)}", level="ERROR")
            return None