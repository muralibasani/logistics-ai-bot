import os
from dotenv import load_dotenv
from langchain.chat_models import init_chat_model

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
MODEL_LOCAL_OLLAMA = os.getenv("MODEL_LOCAL_OLLAMA", "false").lower() == "true"
USE_MOCK_LLM = os.getenv("USE_MOCK_LLM", "false").lower() == "true"
MOCK_LLM_DELAY = float(os.getenv("MOCK_LLM_DELAY", "0.000001"))  # Default 1 microsecond

class LlmModel:
    """Wrapper for initializing and reusing a chat LLM instance."""
    _llm = None  # static cache

    @classmethod
    def get_llm(cls):
        """Return a singleton LLM instance, initializing it if needed."""
        if cls._llm is None:
            # Check if mock LLM is enabled
            if USE_MOCK_LLM:
                from src.mock_llm import MockLLM
                print(f"🔧 Using MOCK LLM (delay: {MOCK_LLM_DELAY}s) - No real API calls")
                cls._llm = MockLLM(delay_ns=MOCK_LLM_DELAY)
            elif MODEL_LOCAL_OLLAMA:
                LLM_MODEL = os.getenv("LLM_MODEL_FREE")
                # Only use model base name
                print(f"🔹 Using Ollama model: {LLM_MODEL}")
                cls._llm = init_chat_model(
                    model=LLM_MODEL,
                    model_provider="ollama",
                    temperature=0,
                )
            else:
                # ✅ Cloud OpenAI model (for production or paid tier)
                if not OPENAI_API_KEY:
                    raise ValueError("❌ Missing OPENAI_API_KEY in environment.")
                LLM_MODEL = os.getenv("LLM_MODEL_PAID", "gpt-4o-mini")
                print(f"🔹 Using OpenAI model: {LLM_MODEL}")
                cls._llm = init_chat_model(
                    model=LLM_MODEL,
                    model_provider="openai",
                    api_key=OPENAI_API_KEY,
                    temperature=0,
                )

        return cls._llm
