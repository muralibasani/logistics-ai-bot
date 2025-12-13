"""
Responder component: Consumes command events, invokes tools, and produces responses.
"""
import json
import logging
import re
from datetime import datetime
from typing import Dict, Any, Optional
from src.tools import (
    get_order_count_tool,
    get_order_status_tool,
    get_order_details_tool,
    cancel_order_tool,
    refund_order_tool
)
from src.kafka_utils.producer import KafkaProducer
from src.kafka_utils.consumer import KafkaConsumer
from src.kafka_utils.config import TOPICS

logger = logging.getLogger(__name__)


class Responder:
    """Responder component that executes tools and produces responses."""
    
    def __init__(self):
        self.producer = KafkaProducer()
        self._consumer = None
        self._running = False
        
        # Map tool names to their actual tool functions
        self.tool_map = {
            "get_order_count_tool": get_order_count_tool,
            "get_order_status_tool": get_order_status_tool,
            "get_order_details_tool": get_order_details_tool,
            "cancel_order_tool": cancel_order_tool,
            "refund_order_tool": refund_order_tool
        }
    
    def _extract_order_id(self, message: str) -> Optional[int]:
        """Extract order ID from message text."""
        # Look for patterns like "order 26", "order id 26", "order #26", etc.
        patterns = [
            r'order\s+(?:id\s+)?#?\s*(\d+)',
            r'order\s+#?\s*(\d+)',
            r'(\d+)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, message, re.IGNORECASE)
            if match:
                try:
                    return int(match.group(1))
                except ValueError:
                    continue
        
        return None
    
    def _invoke_tool(self, tool_name: str, message: str) -> str:
        """
        Invoke the appropriate tool based on tool name and message.
        
        Args:
            tool_name: Name of the tool to invoke
            message: Original user message (used to extract parameters)
            
        Returns:
            Tool response as string
        """
        if tool_name not in self.tool_map:
            return f"Error: Unknown tool '{tool_name}'"
        
        tool = self.tool_map[tool_name]
        
        try:
            # Determine tool parameters based on tool name
            # LangChain tools need to be invoked with .invoke() and a dict of parameters
            if tool_name == "get_order_count_tool":
                return tool.invoke({})
            
            elif tool_name in ["get_order_status_tool", "get_order_details_tool", 
                              "cancel_order_tool", "refund_order_tool"]:
                order_id = self._extract_order_id(message)
                if order_id is None:
                    return f"Error: Could not extract order ID from message: '{message}'"
                return tool.invoke({"order_id": order_id})
            
            else:
                return f"Error: Tool '{tool_name}' not implemented"
                
        except Exception as e:
            logger.error(f"Error invoking tool {tool_name}: {e}", exc_info=True)
            return f"Error executing {tool_name}: {str(e)}"
    
    def process_command(self, message_id: str, tool_name: str, message: str) -> bool:
        """
        Process a command event: invoke the tool and produce response.
        
        Args:
            message_id: Unique message identifier
            tool_name: Name of the tool to invoke
            message: Original user message
            
        Returns:
            True if response was produced successfully, False otherwise
        """
        if not self.producer.connect():
            logger.error("Failed to connect Kafka producer in responder")
            return False
        
        logger.info(f"Processing command: {tool_name} for message_id: {message_id}")
        
        try:
            tool_response = self._invoke_tool(tool_name, message)
            
            event = {
                "message_id": message_id,
                "response": tool_response,
                "tool_name": tool_name,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            success = self.producer.produce(
                topic=TOPICS["output"],
                message=event,
                key=message_id
            )
            
            if success:
                logger.info(f"Response produced to output topic for message_id: {message_id}")
            
            self.producer.flush(timeout=5.0)
            return success
            
        except Exception as e:
            logger.error(f"Error processing command: {e}", exc_info=True)
            # Try to send error response to output topic
            try:
                error_event = {
                    "message_id": message_id,
                    "response": f"Error processing request: {str(e)}",
                    "tool_name": tool_name,
                    "timestamp": datetime.utcnow().isoformat()
                }
                self.producer.produce(
                    topic=TOPICS["output"],
                    message=error_event,
                    key=message_id
                )
                self.producer.flush(timeout=5.0)
            except Exception as send_error:
                logger.error(f"Failed to send error response: {send_error}")
            return False
    
    def start_consumer(self, background: bool = False):
        """
        Start consuming from commands topic and processing commands.
        
        Args:
            background: If True, run consumer in a background thread. If False, block.
        """
        import threading
        
        consumer = KafkaConsumer(
            group_id="responder-consumer-group",
            topics=[TOPICS["commands"]]
        )
        
        if not consumer.connect():
            logger.error("Failed to connect responder consumer")
            raise RuntimeError("Failed to connect Responder consumer to Kafka")
        
        logger.info(f"Responder consumer connected to topic: {TOPICS['commands']}")
        
        def handle_message(message: Dict[str, Any]):
            message_id = message.get("message_id")
            tool_name = message.get("tool_name")
            user_message = message.get("message")
            
            if not message_id or not tool_name or not user_message:
                logger.error(f"Invalid command format: {message}")
                return
            
            try:
                self.process_command(message_id, tool_name, user_message)
            except Exception as e:
                logger.error(f"Error processing command: {e}", exc_info=True)
        
        def consume_loop():
            logger.info("Responder consumer started, listening for commands...")
            try:
                consumer.consume(handle_message)
            except Exception as e:
                logger.error(f"Fatal error in responder consumer loop: {e}", exc_info=True)
                raise
        
        if background:
            self._consumer = consumer
            self._running = True
            consumer_thread = threading.Thread(target=consume_loop, daemon=True, name="responder-consumer")
            consumer_thread.start()
        else:
            try:
                consumer.consume(handle_message)
            except Exception as e:
                logger.error(f"Fatal error in consumer loop: {e}", exc_info=True)
                raise
    
    def close(self):
        """Close the producer and consumer connections."""
        if self._consumer:
            self._running = False
            self._consumer.stop()
            self._consumer.close()
        self.producer.close()

