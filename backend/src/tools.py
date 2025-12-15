"""
Agent setup for order management with tools.
"""
from email import message
from langchain_core.tools import tool
from src.llm import LlmModel
import logging

logger = logging.getLogger(__name__)

llm = LlmModel.get_llm()


# Create structured tools for LangChain
@tool
def get_order_count_tool() -> str:
    """Get the total count of orders and count by status. Use this when user asks about total number of orders or order counts."""
    from src.order_service import get_order_count
    try:
        result = get_order_count()
        return f"Total orders: {result['total_orders']}. Orders by status: {result['by_status']}"
    except Exception as e:
        return f"Error getting order count: {str(e)}"


@tool
def get_order_status_tool(order_id: int) -> str:
    """Get the status and details of a specific order. Use this when user asks about order status, whether order exists, or if order CAN be cancelled/refunded (checking eligibility). This tool only CHECKS eligibility - it does NOT execute cancellation or refund. 

IMPORTANT: Use this tool for questions like:
- 'can we cancel order X?'
- 'can you cancel order X?'
- 'is order X eligible for refund?'
- 'can you refund order X?'
- 'can order X be refunded?'
- 'can order X be cancelled?'

These are QUESTIONS asking IF something can be done - NOT commands to DO it. This tool will return yes/no eligibility information only."""
    from src.order_service import get_order_status
    try:
        result = get_order_status(order_id)
        if not result.get("exists"):
            return f"Order {order_id} does not exist. Therefore, it cannot be cancelled or refunded."
        
        status = result.get('status')
        has_cancellation = result.get("has_cancellation", False)
        has_refund = result.get("has_refund", False)
        
        # Build eligibility information
        status_info = f"Order {order_id} status: {status}"
        if result.get("total_amount"):
            status_info += f", Total amount: ${result.get('total_amount')}"
        
        # Determine cancellation eligibility
        can_cancel = True
        cancel_reason = ""
        if has_cancellation or has_refund or status in ['Cancelled', 'Refunded']:
            can_cancel = False
            if has_cancellation:
                cancel_reason = "already has a cancellation record"
            elif has_refund:
                cancel_reason = "already has a refund record"
            elif status in ['Cancelled', 'Refunded']:
                cancel_reason = f"order status is '{status}'"
        
        # Determine refund eligibility
        can_refund = True
        refund_reason = ""
        if has_cancellation or has_refund or status in ['Cancelled', 'Refunded']:
            can_refund = False
            if has_cancellation:
                refund_reason = "already has a cancellation record"
            elif has_refund:
                refund_reason = "already has a refund record"
            elif status in ['Cancelled', 'Refunded']:
                refund_reason = f"order status is '{status}'"
        
        # Add eligibility information
        status_info += f"\n\nCancellation Eligibility: {'Yes, order can be cancelled' if can_cancel else f'No, order cannot be cancelled ({cancel_reason})'}"
        status_info += f"\nRefund Eligibility: {'Yes, order can be refunded' if can_refund else f'No, order cannot be refunded ({refund_reason})'}"
        
        return status_info
    except Exception as e:
        return f"Error getting order status: {str(e)}"


@tool
def cancel_order_tool(order_id: int) -> str:
    """Cancel an order by updating its status and creating a cancellation record. Use this ONLY when user explicitly wants to EXECUTE cancellation.

IMPORTANT: Use this tool for EXECUTION commands, even if they contain question words. Look for execution keywords:
- 'cancel order X'
- 'execute cancellation for order X' (even if phrased as 'can you execute cancellation')
- 'proceed with cancellation for order X'
- 'go ahead and cancel order X'
- 'please cancel order X'
- 'perform cancellation for order X'
- 'do cancellation for order X'

CRITICAL: If the message contains execution keywords like 'execute', 'proceed', 'go ahead', 'perform', 'do', or direct action verbs like 'cancel', use this tool EVEN IF the message also contains 'can you' or question words.

DO NOT use this tool ONLY for pure questions without execution intent:
- 'can you cancel order X?' (no execution keywords) → Use get_order_status_tool
- 'can we cancel order X?' (no execution keywords) → Use get_order_status_tool
- 'is order X eligible for cancellation?' (no execution keywords) → Use get_order_status_tool

If the message has BOTH question words AND execution keywords (like 'can you execute cancellation'), prioritize the execution intent and use this tool."""
    from src.order_service import cancel_order
    try:
        result = cancel_order(order_id)
        return result.get("message", "Unknown error")
    except Exception as e:
        return f"Error cancelling order: {str(e)}"


@tool
def refund_order_tool(order_id: int) -> str:
    """Refund an order by updating its status and creating a refund record. Use this ONLY when user explicitly wants to EXECUTE refund.

IMPORTANT: Use this tool for EXECUTION commands, even if they contain question words. Look for execution keywords:
- 'refund order X'
- 'execute refund for order X' (even if phrased as 'can you execute refund')
- 'proceed with refund for order X'
- 'go ahead and refund order X'
- 'please refund order X'
- 'perform refund for order X'
- 'do refund for order X'

CRITICAL: If the message contains execution keywords like 'execute', 'proceed', 'go ahead', 'perform', 'do', or direct action verbs like 'refund', use this tool EVEN IF the message also contains 'can you' or question words.

DO NOT use this tool ONLY for pure questions without execution intent:
- 'can you refund order X?' (no execution keywords) → Use get_order_status_tool
- 'can we refund order X?' (no execution keywords) → Use get_order_status_tool
- 'is order X eligible for refund?' (no execution keywords) → Use get_order_status_tool

If the message has BOTH question words AND execution keywords (like 'can you execute refund'), prioritize the execution intent and use this tool."""
    from src.order_service import refund_order
    try:
        result = refund_order(order_id)
        message = result.get("message", "Unknown error")
        if result.get("success") and result.get("refund_amount"):
            message += f" Refund amount: ${result.get('refund_amount')}"
        return message
    except Exception as e:
        return f"Error refunding order: {str(e)}"


@tool
def get_order_details_tool(order_id: int) -> str:
    """Get comprehensive details of an order including customer information, order items, tracking history, cancellation info, refund info, and delivery information. Use this when user asks for detailed information about an order, wants to see order items, customer details, tracking history, or full order information."""
    from src.order_service import get_order_details
    try:
        result = get_order_details(order_id)
        if not result.get("exists"):
            return f"Order {order_id} does not exist."
        
        # Format the response in a readable way
        details = []
        details.append(f"Order ID: {result.get('order_id')}")
        details.append(f"Status: {result.get('order_status')}")
        details.append(f"Order Date: {result.get('order_date')}")
        details.append(f"Total Amount: {result.get('total_amount')}")
        
        if result.get("customer_name"):
            details.append(f"\nCustomer Information:")
            details.append(f"  Name: {result.get('customer_name')}")
            if result.get("customer_email"):
                details.append(f"  Email: {result.get('customer_email')}")
            if result.get("customer_phone"):
                details.append(f"  Phone: {result.get('customer_phone')}")
        
        if result.get("items"):
            details.append(f"\nOrder Items ({len(result.get('items', []))}):")
            for item in result.get("items", []):
                details.append(f"  - {item.get('product_name')}: Quantity {item.get('quantity')}, Price ${item.get('price')}")
        
        if result.get("tracking"):
            details.append(f"\nTracking History:")
            for track in result.get("tracking", []):
                location = f" at {track.get('location')}" if track.get('location') else ""
                timestamp = f" on {track.get('timestamp')}" if track.get('timestamp') else ""
                details.append(f"  - {track.get('status')}{location}{timestamp}")
        
        if result.get("cancellation"):
            cancel = result.get("cancellation")
            details.append(f"\nCancellation Information:")
            details.append(f"  Date: {cancel.get('cancel_date')}")
            details.append(f"  Reason: {cancel.get('reason')}")
            details.append(f"  Cancelled by: {cancel.get('cancelled_by')}")
        
        if result.get("refund"):
            refund = result.get("refund")
            details.append(f"\nRefund Information:")
            details.append(f"  Date: {refund.get('refund_date')}")
            details.append(f"  Amount: ${refund.get('refund_amount')}")
            details.append(f"  Status: {refund.get('refund_status')}")
        
        if result.get("delivery"):
            delivery = result.get("delivery")
            details.append(f"\nDelivery Information:")
            details.append(f"  Delivered Date: {delivery.get('delivered_date')}")
            details.append(f"  Delivery Person: {delivery.get('delivery_person')}")
            if delivery.get("comments"):
                details.append(f"  Comments: {delivery.get('comments')}")
        
        return "\n".join(details)
    except Exception as e:
        return f"Error getting order details: {str(e)}"
    

@tool
def default_tool(user_message: str) -> str:
    """Handle general conversational messages like greetings, thanks, farewells, compliments, or general questions that don't require order management tools. Use this for: greetings (hello, hi, hey), thanks (thank you, thanks), farewells (bye, goodbye, see you), compliments (good job, well done), or general conversation."""
    import os
    from dotenv import load_dotenv
    
    load_dotenv()
    USE_MOCK_LLM = os.getenv("USE_MOCK_LLM", "false").lower() == "true"
    MOCK_LLM_DELAY = float(os.getenv("MOCK_LLM_DELAY", "0.000001"))
    
    # Use mock LLM if enabled
    if USE_MOCK_LLM:
        from src.mock_llm import mock_default_tool
        return mock_default_tool(user_message, delay_ns=MOCK_LLM_DELAY)
    
    # Use real LLM
    from langchain_core.messages import SystemMessage, HumanMessage
    
    # Create a friendly, context-aware system prompt for conversational responses
    conversational_prompt = """You are a friendly and helpful order management assistant. 
    
Respond naturally and warmly to:
- Greetings: Respond warmly and offer to help with order management
- Thanks/Appreciation: Acknowledge graciously and offer continued assistance
- Farewells: Say goodbye politely and wish them well
- Compliments: Accept graciously and offer to help further
- General questions: Answer helpfully, and if relevant, mention you can help with order management

Keep responses concise, friendly, and professional. If the message is unclear, politely ask how you can help with their orders."""
    
    messages = [
        SystemMessage(content=conversational_prompt),
        HumanMessage(content=user_message)
    ]
    
    try:
        response = llm.invoke(messages)
        return response.content if hasattr(response, 'content') else str(response)
    except Exception as e:
        logger.error(f"Error in default_tool: {e}", exc_info=True)
        # Fallback responses based on message content
        message_lower = user_message.lower()
        if any(word in message_lower for word in ['hello', 'hi', 'hey', 'greetings']):
            return "Hello! I'm here to help you with order management. How can I assist you today?"
        elif any(word in message_lower for word in ['thank', 'thanks', 'appreciate']):
            return "You're welcome! I'm happy to help. Is there anything else you need with your orders?"
        elif any(word in message_lower for word in ['bye', 'goodbye', 'see you', 'farewell']):
            return "Goodbye! Have a great day, and feel free to come back if you need help with your orders!"
        else:
            return "I'm here to help you with order management. How can I assist you today?"


# Define tools list for the agent
order_tools = [
    get_order_count_tool,
    get_order_status_tool,
    get_order_details_tool,
    cancel_order_tool,
    refund_order_tool
]

# Combined tools list (order tools + default conversational tool)
all_tools = [
    *order_tools,
    default_tool
]




