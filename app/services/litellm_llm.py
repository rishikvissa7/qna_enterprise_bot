from langchain.chat_models import ChatLiteLLM  # LangChain's wrapper for LiteLLM-supported chat models
import os  # To access environment variables

def get_litellm_chat_model():
    """
    Initializes and returns a ChatLiteLLM instance configured to use
    the Together.ai-hosted Mistral 7B model for chat generation.

    Returns:
    - A ChatLiteLLM object that can be used like an LLM in LangChain.
    """
    return ChatLiteLLM(
        model="together_ai/mistralai/Mistral-7B-Instruct-v0.2",  # Model from Together.ai
        api_key=os.getenv("TOGETHER_API_KEY"),  # Read API key from environment variable
        temperature=0.7,  # Controls randomness (0 = deterministic, 1 = creative)
        max_tokens=1024,  # Maximum length of the model's response
    )
