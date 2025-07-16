from langchain.chat_models import ChatLiteLLM
import os

def get_litellm_chat_model():
    return ChatLiteLLM(
        model="together_ai/mistralai/Mistral-7B-Instruct-v0.2",
        api_key=os.getenv("TOGETHER_API_KEY"),
        temperature=0.7,
        max_tokens=1024,
    )