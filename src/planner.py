"""
Planner component: Classifies messages and produces command events to Kafka.
"""
import json
import logging
import uuid
from datetime import datetime
from typing import Dict, Any, Optional
from langchain_core.messages import HumanMessage, SystemMessage
from langchain.agents import create_agent
from src.llm import LlmModel
from src.models import ResponseFormat, Context
from src.tools import (
    get_order_count_tool,
    get_order_status_tool,
    get_order_details_tool,
    cancel_order_tool,
    refund_order_tool,
    default_tool
)
from src.kafka_utils.producer import KafkaProducer
from src.kafka_utils.consumer import KafkaConsumer
from src.kafka_utils.config import TOPICS

logger = logging.getLogger(__name__)


class Planner:
    """Planner component that classifies messages and produces command events."""
    
    def __init__(self):
        self.llm = LlmModel.get_llm()
        self.producer = KafkaProducer()
        self.tools = [
            get_order_count_tool,
            get_order_status_tool,
            get_order_details_tool,
            cancel_order_tool,
            refund_order_tool,
            default_tool
        ]
        
        # Create agent for classification
        self.agent = create_agent(
            model=self.llm,
            tools=self.tools,
            system_prompt="""You are an order management assistant.

CRITICAL DISTINCTION: There is a difference between CHECKING eligibility and EXECUTING actions:

1. CHECKING ELIGIBILITY (use get_order_status_tool):
   - Pure questions asking IF something can be done (WITHOUT execution keywords):
     * "can we cancel order 3?" (no execution keywords)
     * "can you cancel order 3?" (no execution keywords)
     * "is order 3 eligible for refund?" (no execution keywords)
     * "can you refund order 3?" (no execution keywords)
     * "can order 3 be cancelled?" (no execution keywords)
     * "can order 3 be refunded?" (no execution keywords)
   - These questions ask IF something CAN be done, not to DO it
   - Use get_order_status_tool to check eligibility and respond with yes/no
   - Do NOT execute the cancellation/refund, just check and inform
   - The tool will return eligibility information (yes/no) without performing any action

2. EXECUTING ACTIONS (use cancel_order_tool or refund_order_tool):
   - Messages with EXECUTION KEYWORDS (even if they also contain question words):
     * "cancel order 3"
     * "execute cancellation for order 3"
     * "can you execute cancellation for order 3?" (has 'execute' keyword - USE EXECUTION TOOL)
     * "can you execute refund for order 1?" (has 'execute' keyword - USE EXECUTION TOOL)
     * "proceed with refund for order 5"
     * "refund order 3"
     * "go ahead and cancel order 3"
     * "please refund order 3"
     * "perform refund for order X"
     * "do cancellation for order X"
   - These are explicit requests to PERFORM the action
   - Use cancel_order_tool or refund_order_tool to actually execute the cancellation/refund
   - These tools will modify the database and perform the actual cancellation/refund

KEY RULE: 
- EXECUTION KEYWORDS take priority: If the message contains execution keywords like "execute", "proceed", "go ahead", "perform", "do", or direct action verbs like "cancel"/"refund", use the execution tool (cancel_order_tool or refund_order_tool) EVEN IF the message also contains question words like "can you".
- Only use get_order_status_tool for PURE questions without any execution keywords.
- Examples:
  * "can you execute refund for order 1?" → Has "execute" keyword → Use refund_order_tool
  * "can you refund order 1?" → No execution keywords → Use get_order_status_tool
  * "execute cancellation for order 3" → Has "execute" keyword → Use cancel_order_tool
  * "can we cancel order 3?" → No execution keywords → Use get_order_status_tool

Step 1: Based on the user's message, call exactly **one** of the available tools:

- get_order_count_tool: When user asks about total number of orders or order counts
- get_order_status_tool: When user asks about order status, whether order exists, or if order CAN be cancelled/refunded (checking eligibility - questions like "can we cancel?", "can you refund?", "is it eligible?")
- get_order_details_tool: When user asks for detailed information about an order, wants to see order items, customer details, tracking history, or full order information
- cancel_order_tool: When user explicitly wants to EXECUTE cancellation (commands like "cancel order X", "execute cancellation", "proceed with cancellation") - NOT for questions
- refund_order_tool: When user explicitly wants to EXECUTE refund (commands like "refund order X", "execute refund", "proceed with refund") - NOT for questions
- default_tool: When the user is greeting (hello, hi, hey), saying thanks (thank you, thanks), saying goodbye (bye, goodbye), giving compliments, or having general conversation that doesn't require order management operations

After calling the correct tool, **do not call any further tools**.

Return only the final assistant message in plain text.
""",
            response_format=ResponseFormat,
            context_schema=Context
        )
        
        # Map tool names to their actual tool objects
        self.tool_map = {
            "get_order_count_tool": get_order_count_tool,
            "get_order_status_tool": get_order_status_tool,
            "get_order_details_tool": get_order_details_tool,
            "cancel_order_tool": cancel_order_tool,
            "refund_order_tool": refund_order_tool,
            "default_tool": default_tool
        }
        
        # Order tools that should be sent to commands topic
        self.order_tools = {
            "get_order_count_tool",
            "get_order_status_tool",
            "get_order_details_tool",
            "cancel_order_tool",
            "refund_order_tool"
        }
    
    def _classify_message(self, message: str) -> Optional[str]:
        """
        Classify a message to determine which tool should be used.
        Returns the tool name if it's an order tool, None otherwise.
        """
        try:
            # Use a simpler classification prompt that just identifies the tool
            classification_prompt = """You are a message classifier for an order management system.

Based on the user's message, identify which tool should be used. Return ONLY the tool name, nothing else.

Available order tools:
- get_order_count_tool: For questions about total number of orders or order counts
- get_order_status_tool: For questions about order status, whether order exists, or if order CAN be cancelled/refunded (checking eligibility - questions like "can we cancel?", "can you refund?", "is it eligible?")
- get_order_details_tool: For questions about detailed information about an order, wants to see order items, customer details, tracking history, or full order information
- cancel_order_tool: For explicit EXECUTION commands to cancel (commands like "cancel order X", "execute cancellation", "proceed with cancellation") - NOT for questions
- refund_order_tool: For explicit EXECUTION commands to refund (commands like "refund order X", "execute refund", "proceed with refund") - NOT for questions

CRITICAL RULES:
- EXECUTION KEYWORDS take priority: If message contains "execute", "proceed", "go ahead", "perform", "do", or direct action verbs like "cancel"/"refund", use the execution tool EVEN IF it contains question words.
- Only use get_order_status_tool for PURE questions without execution keywords.
- If the message is a greeting, thanks, farewell, or general conversation, return "default_tool"

Return ONLY the tool name (e.g., "get_order_details_tool") or "default_tool" if it's not an order-related message."""

            classification_messages = [
                SystemMessage(content=classification_prompt),
                HumanMessage(content=f"Classify this message: {message}")
            ]
            
            response = self.llm.invoke(classification_messages)
            tool_name = response.content.strip() if hasattr(response, 'content') else str(response).strip()
            
            # Clean up the tool name (remove quotes, extra text)
            tool_name = tool_name.replace('"', '').replace("'", "").strip()
            
            # Check if it's an order tool
            if tool_name in self.order_tools:
                return tool_name
            elif tool_name == "default_tool":
                return None
            else:
                # Try to find a matching tool name in the response
                for order_tool in self.order_tools:
                    if order_tool.lower() in tool_name.lower():
                        return order_tool
                return None
            
        except Exception as e:
            logger.error(f"Error classifying message: {e}", exc_info=True)
            return None
    
    def process_message(self, message_id: str, message: str) -> bool:
        """
        Process a message: classify it and produce to commands topic if it's an order tool.
        For non-order tools (like greetings), handle directly and produce to output topic.
        
        Args:
            message_id: Unique message identifier
            message: User message content
            
        Returns:
            True if message was processed successfully, False otherwise
        """
        if not self.producer.connect():
            logger.error("Failed to connect Kafka producer in planner")
            return False
        
        # Classify the message
        tool_name = self._classify_message(message)
        
        if tool_name and tool_name in self.order_tools:
            # Create command event for order tools
            event = {
                "message_id": message_id,
                "tool_name": tool_name,
                "message": message,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            # Produce to commands topic
            success = self.producer.produce(
                topic=TOPICS["commands"],
                message=event,
                key=message_id
            )
            
            if success:
                logger.info("")
                logger.info("📋 [PLANNER] Message classified and command produced")
                logger.info(f"   Message ID: {message_id}")
                logger.info(f"   Tool: {tool_name}")
                logger.info(f"   Message: {message}")
                logger.info("")
            
            self.producer.flush(timeout=5.0)
            return success
        else:
            # Message doesn't require an order tool (e.g., greeting, default_tool)
            # These should not reach the planner - they should be handled by the gateway
            logger.warning(f"[PLANNER] Message '{message}' classified as non-order tool, but it reached planner. This should not happen.")
            return False
    
    def start_consumer(self):
        """Start consuming from raw input topic and processing messages."""
        consumer = KafkaConsumer(
            group_id="planner-consumer-group",
            topics=[TOPICS["commands"]]
        )
        
        if not consumer.connect():
            logger.error("Failed to connect planner consumer")
            return
        
        def handle_message(message: Dict[str, Any]):
            message_id = message.get("message_id")
            user_message = message.get("message")
            
            if not message_id or not user_message:
                logger.error(f"Invalid message format: {message}")
                return
            
            logger.info("")
            logger.info("📥 [PLANNER] Received message for classification")
            logger.info(f"   Message ID: {message_id}")
            logger.info(f"   User Message: {user_message}")
            logger.info("")
            
            self.process_message(message_id, user_message)
        
        logger.info("Starting planner consumer...")
        consumer.consume(handle_message)
    
    def close(self):
        """Close the producer connection."""
        self.producer.close()

