from qdrant_client import QdrantClient  # Qdrant client for vector DB operations
from qdrant_client.models import PointStruct, VectorParams  # (Only PointStruct/VectorParams needed for other use cases)
from sentence_transformers import SentenceTransformer  # Used to convert text to embeddings (vectors)
import os  # For reading environment variables


# Configuration: Connect to Qdrant Server
# Get Qdrant credentials from environment
QDRANT_URL = os.getenv("QDRANT_URL")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")

# Create a Qdrant client instance for making queries
client = QdrantClient(url=QDRANT_URL, api_key=QDRANT_API_KEY)

# Load a sentence embedding model to convert text → vector
# "all-MiniLM-L6-v2" is a lightweight model good for semantic search
model = SentenceTransformer("all-MiniLM-L6-v2")


# Function: Search a Vector Collection

def search_collection(collection_name: str, query: str, top_k: int = 5):
    """
    Search for the most relevant documents in a given Qdrant collection.

    Parameters:
    - collection_name: Name of the Qdrant vector collection to search
    - query: The search string (user input)
    - top_k: How many top results to return

    Returns:
    - A list of dictionaries with the matched question, answer, and similarity score
    """
    # Step 1: Convert query string into a dense vector using SentenceTransformer
    vector = model.encode(query)

    # Step 2: Perform similarity search in the vector DB
    hits = client.search(
        collection_name=collection_name,  # Target collection
        query_vector=vector,              # Vectorized user input
        limit=top_k                       # Number of results to return
    )

    # Step 3: Extract and format relevant fields from each result
    return [
        {
            "question": h.payload["question"],  # Original stored question
            "answer": h.payload["answer"],      # Associated answer
            "score": h.score                    # Similarity score (higher = better match)
        }
        for h in hits
    ]
