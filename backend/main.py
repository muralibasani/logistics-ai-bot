"""
Main entry point: Gateway component that handles user input/output via Kafka.
"""
import uuid
import logging
import threading
import time
from typing import Dict, Any, Optional
from dotenv import load_dotenv
from langchain_core.messages import HumanMessage, SystemMessage
from src.llm import LlmModel
from src.kafka_utils.producer import KafkaProducer
from src.kafka_utils.consumer import KafkaConsumer
from src.kafka_utils.config import TOPICS
from src.tools import default_tool
from src.responder import Responder

load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class Gateway:
    """Gateway component that handles user interactions via Kafka."""
    
    def __init__(self):
        self.producer = KafkaProducer()
        self.consumer: Optional[KafkaConsumer] = None
        self.pending_responses: Dict[str, str] = {}  # message_id -> response
        self.conversation_id = str(uuid.uuid4())
        self.running = False
        self.llm = LlmModel.get_llm()
        
        # Order tools that should go through Kafka
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
        Returns the tool name if it's an order tool, None for default_tool.
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
            else:
                return None  # default_tool or unknown
            
        except Exception as e:
            logger.error(f"Error classifying message: {e}", exc_info=True)
            return None
    
    def process_message(self, user_message: str) -> str:
        """
        Process a user message. If it's an order tool, send to Kafka.
        If it's a default tool, handle directly and return response.
        
        Args:
            user_message: User's input message
            
        Returns:
            message_id: Unique identifier for this message (always returned)
        """
        message_id = str(uuid.uuid4())
        
        logger.debug(f"New user message received: {user_message}")
        
        # Classify the message
        tool_name = self._classify_message(user_message)
        
        if tool_name and tool_name in self.order_tools:
            # Order tool - send to Kafka commands topic
            if not self.producer.connect():
                logger.error("Failed to connect Kafka producer")
                raise RuntimeError("Failed to connect to Kafka")
            
            from datetime import datetime
            
            event = {
                "message_id": message_id,
                "tool_name": tool_name,
                "message": user_message,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            success = self.producer.produce(
                topic=TOPICS["commands"],
                message=event,
                key=message_id
            )
            
            if not success:
                raise RuntimeError("Failed to send message to Kafka")
            
            self.producer.flush(timeout=5.0)
            
            logger.info(f"Message sent to commands topic (tool: {tool_name}, message_id: {message_id})")
            return message_id
        else:
            # Default tool - handle directly without Kafka
            logger.debug("Message classified as default tool, handling directly")
            
            try:
                # default_tool is a LangChain StructuredTool, so we need to use .invoke()
                response = default_tool.invoke({"user_message": user_message})
                # Store response so it can be retrieved
                self.pending_responses[message_id] = response
                return message_id
            except Exception as e:
                logger.error(f"Error handling default tool: {e}", exc_info=True)
                error_response = "I'm here to help you with order management. How can I assist you today?"
                self.pending_responses[message_id] = error_response
                return message_id
    
    def start_consumer(self):
        """Start consuming responses from output topic."""
        self.consumer = KafkaConsumer(
            group_id="gateway-consumer-group",
            topics=[TOPICS["output"]]
        )
        
        if not self.consumer.connect():
            logger.error("Failed to connect output consumer")
            return
        
        def handle_message(message: Dict[str, Any]):
            message_id = message.get("message_id", "unknown")
            response = message.get("response", "")
            
            logger.info(f"Received response for message_id: {message_id}")
            # Store response for the message_id
            self.pending_responses[message_id] = response
        
        self.running = True
        
        # Start consumer in a separate thread
        def consume_loop():
            logger.info("Starting gateway output consumer...")
            self.consumer.consume(handle_message)
        
        consumer_thread = threading.Thread(target=consume_loop, daemon=True)
        consumer_thread.start()
    
    def wait_for_response(self, message_id: str, timeout: float = 30.0) -> Optional[str]:
        """
        Wait for a response for the given message_id.
        
        Args:
            message_id: Message identifier to wait for
            timeout: Maximum time to wait in seconds
            
        Returns:
            Response string if received, None if timeout
        """
        start_time = time.time()
        while time.time() - start_time < timeout:
            if message_id in self.pending_responses:
                response = self.pending_responses.pop(message_id)
                return response
            time.sleep(0.1)
        
        logger.warning(f"Timeout waiting for response to message_id: {message_id}")
        return None
    
    def close(self):
        """Close producer and consumer connections."""
        if self.consumer:
            self.consumer.stop()
            self.consumer.close()
        self.producer.close()
        self.running = False


def main():
    """Main entry point for the CLI gateway."""
    print("🚀 Logistics AI Bot - Kafka Event-Driven Architecture")
    print("=" * 60)
    print("Starting gateway and responder services...")
    print("=" * 60)
    print()
    
    gateway = Gateway()
    responder = Responder()
    
    try:
        # Start Responder consumer in background (consumes from commands topic)
        logger.info("Starting Responder service in background...")
        responder.start_consumer(background=True)
        
        # Start Gateway consumer in background (consumes from output topic)
        logger.info("Starting Gateway consumer in background...")
        gateway.start_consumer()
        
        # Give consumers time to connect
        time.sleep(2)
        
        print("✅ All services started!")
        print("Gateway ready! Type your messages (or 'exit' to quit):\n")
        
        while True:
            user_input = input("You: ").strip()
            
            if user_input.lower() in ["exit", "quit"]:
                print("\n🙏 Thank you for using the AI assistant!")
                break
            
            if not user_input:
                continue
            
            try:
                # Process message (sends to Kafka if order tool, handles directly if default tool)
                message_id = gateway.process_message(user_input)
                
                if message_id:
                    # Check if response is already available (default tool handled directly)
                    if message_id in gateway.pending_responses:
                        response = gateway.pending_responses.pop(message_id)
                        print(f"\n🤖 Assistant: {response}\n")
                    else:
                        # Order tool - wait for Kafka response
                        print("\n⏳ Processing...")
                        response = gateway.wait_for_response(message_id, timeout=30.0)
                        
                        if response:
                            print(f"\n🤖 Assistant: {response}\n")
                        else:
                            print("\n❌ No response received (timeout or error)\n")
                else:
                    print("\n❌ Failed to process message\n")
                    
            except Exception as e:
                logger.error(f"Error processing message: {e}", exc_info=True)
                print(f"\n❌ Error: {str(e)}\n")
    
    except KeyboardInterrupt:
        print("\n\n👋 Shutting down...")
    finally:
        responder.close()
        gateway.close()
        logger.info("All services shutdown complete")


if __name__ == "__main__":
    main()
