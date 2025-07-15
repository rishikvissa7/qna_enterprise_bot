import vertexai
from vertexai.language_models import ChatModel

import os

def get_vertex_chat_model():
    project_id = os.getenv("GOOGLE_PROJECT_ID")
    location = os.getenv("GOOGLE_LOCATION", "us-central1")

    vertexai.init(project=project_id, location=location)
    chat_model = ChatModel.from_pretrained("gemini-1.5-pro-preview-0409")

    return chat_model.start_chat()
