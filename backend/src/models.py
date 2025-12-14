from dataclasses import dataclass

@dataclass
class ResponseFormat:
    """Agent structured output."""
    final_response: str
    reasoning_path: str | None = None

@dataclass
class Context:
    user_id: str
