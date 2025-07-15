from qdrant_client import QdrantClient
from qdrant_client.models import PointStruct, VectorParams
from sentence_transformers import SentenceTransformer
import os

QDRANT_URL = os.getenv("QDRANT_URL")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")
client = QdrantClient(url=QDRANT_URL, api_key=QDRANT_API_KEY)
model = SentenceTransformer("all-MiniLM-L6-v2")

def search_collection(collection_name: str, query: str, top_k: int = 5):
    vector = model.encode(query)
    hits = client.search(
        collection_name=collection_name,
        query_vector=vector,
        limit=top_k
    )
    return [{"question": h.payload["question"], "answer": h.payload["answer"], "score": h.score} for h in hits]
