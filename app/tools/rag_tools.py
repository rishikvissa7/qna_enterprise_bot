from langchain.tools import tool
from app.services.qdrant_search import search_collection

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
    """Search Microsoft collection"""
    return search_collection("tesla", query)

@tool
def tcs_rag_tool(query: str):
    """Search Meta collection"""
    return search_collection("tcs", query)
