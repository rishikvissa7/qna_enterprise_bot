# Import LangChain's tool decorator
from langchain.tools import tool

# Import the function that performs a semantic search from Qdrant
from app.services.qdrant_search import search_collection



# Each @tool creates a LangChain-compatible tool
# These are used by the agent to query specific company collections

@tool
def google_rag_tool(query: str):
    """Search Google collection"""
    return search_collection("google", query)

@tool
def apple_rag_tool(query: str):
    """Search Apple collection"""
    return search_collection("apple", query)

@tool
def amazon_rag_tool(query: str):
    """Search Amazon collection"""
    return search_collection("amazon", query)

@tool
def tesla_rag_tool(query: str):
    """Search Tesla collection""" 
    return search_collection("tesla", query)

@tool
def tcs_rag_tool(query: str):
    """Search TCS collection"""  
    return search_collection("tcs", query)