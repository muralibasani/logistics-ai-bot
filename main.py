import os
from dotenv import load_dotenv
from src.llm import LlmModel
from src.models import Context, ResponseFormat
from src.tools import get_order_count_tool, get_order_status_tool, get_order_details_tool, cancel_order_tool, refund_order_tool, default_tool
from langchain_core.messages import HumanMessage, AIMessage
from langchain.agents import create_agent

load_dotenv()


def main():
    print("Hello from workshop4!")

    llm = LlmModel.get_llm()

    tools = [
        get_order_count_tool,
        get_order_status_tool,
        get_order_details_tool,
        cancel_order_tool,
        refund_order_tool,
        default_tool
    ]

    agent = create_agent(
        model=llm,
        tools=tools,
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

    config = {"configurable": {"conversation_id": "workshop4_order_management"}}

    while True:
        query = input("You : ")
        if query.lower() in ["exit", "quit"]:
            print(f"🙏 Thank you for using ai assistant!")
            break

        agent_messages = [HumanMessage(content=query)]  # create new list
        response_obj = agent.invoke({"messages": agent_messages}, config=config)
        response = response_obj['structured_response'].final_response
        print(f"\n🤖 Assistant: {response}")


if __name__ == "__main__":
    main()
