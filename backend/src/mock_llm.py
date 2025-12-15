"""
Mock LLM implementation for benchmarking and testing without real API calls.
Provides fast, deterministic responses with minimal delay.
"""
import time
import os
from typing import List, Any
from langchain_core.messages import BaseMessage, SystemMessage, HumanMessage


class MockLLMResponse:
    """Mock response object that mimics LangChain LLM response."""
    
    def __init__(self, content: str):
        self.content = content


class MockLLM:
    """Mock LLM that returns fast responses without real API calls."""
    
    def __init__(self, delay_ns: float = 0.000001):  # Default 1 microsecond delay
        """
        Initialize mock LLM.
        
        Args:
            delay_ns: Delay in seconds (default 0.000001 = 1 microsecond)
        """
        self.delay = delay_ns
    
    def invoke(
        self,
        messages: List[BaseMessage],
        config: Any = None,
        stop: List[str] = None,
        **kwargs: Any
    ) -> MockLLMResponse:
        """
        Mock invoke method that returns a response after minimal delay.
        
        Args:
            messages: List of messages (SystemMessage, HumanMessage, etc.)
            config: Optional configuration
            stop: Optional stop sequences
            **kwargs: Additional arguments
            
        Returns:
            MockLLMResponse with generated content
        """
        # Simulate minimal processing delay
        time.sleep(self.delay)
        
        # Extract the last human message to generate a context-aware response
        human_message = None
        system_message = None
        
        for msg in messages:
            if isinstance(msg, HumanMessage):
                human_message = msg.content if hasattr(msg, 'content') else str(msg)
            elif isinstance(msg, SystemMessage):
                system_message = msg.content if hasattr(msg, 'content') else str(msg)
        
        # Generate mock response based on context
        if system_message and "classifier" in system_message.lower():
            # Classification response - return a tool name
            if human_message:
                msg_lower = human_message.lower()
                if "order" in msg_lower and ("detail" in msg_lower or "info" in msg_lower):
                    response = "get_order_details_tool"
                elif "order" in msg_lower and ("status" in msg_lower or "cancel" in msg_lower or "refund" in msg_lower):
                    if "cancel" in msg_lower or "refund" in msg_lower:
                        # Check if it's a question or command
                        if any(word in msg_lower for word in ["can", "is", "what", "how"]):
                            response = "get_order_status_tool"
                        else:
                            response = "cancel_order_tool" if "cancel" in msg_lower else "refund_order_tool"
                    else:
                        response = "get_order_status_tool"
                elif "count" in msg_lower or "how many" in msg_lower:
                    response = "get_order_count_tool"
                elif any(word in msg_lower for word in ["hello", "hi", "hey", "thanks", "thank", "bye", "goodbye"]):
                    response = "default_tool"
                else:
                    response = "default_tool"
            else:
                response = "default_tool"
        else:
            # Conversational response
            if human_message:
                msg_lower = human_message.lower()
                if any(word in msg_lower for word in ["hello", "hi", "hey", "greetings"]):
                    response = "Hello! I'm here to help you with order management. How can I assist you today?"
                elif any(word in msg_lower for word in ["thank", "thanks", "appreciate"]):
                    response = "You're welcome! I'm happy to help. Is there anything else you need with your orders?"
                elif any(word in msg_lower for word in ["bye", "goodbye", "see you", "farewell"]):
                    response = "Goodbye! Have a great day, and feel free to come back if you need help with your orders!"
                else:
                    response = "I'm here to help you with order management. How can I assist you today?"
            else:
                response = "I'm here to help you with order management. How can I assist you today?"
        
        return MockLLMResponse(content=response)


def mock_default_tool(user_message: str, delay_ns: float = 0.000001) -> str:
    """
    Mock version of default_tool for benchmarks.
    
    Args:
        user_message: User's message
        delay_ns: Delay in seconds (default 0.000001 = 1 microsecond)
        
    Returns:
        Mock conversational response
    """
    # Simulate minimal processing delay
    time.sleep(delay_ns)
    
    message_lower = user_message.lower()
    if any(word in message_lower for word in ['hello', 'hi', 'hey', 'greetings']):
        return "Hello! I'm here to help you with order management. How can I assist you today?"
    elif any(word in message_lower for word in ['thank', 'thanks', 'appreciate']):
        return "You're welcome! I'm happy to help. Is there anything else you need with your orders?"
    elif any(word in message_lower for word in ['bye', 'goodbye', 'see you', 'farewell']):
        return "Goodbye! Have a great day, and feel free to come back if you need help with your orders!"
    else:
        return "I'm here to help you with order management. How can I assist you today?"

