# app/api/query_router.py

# Import FastAPI tools for building APIs
from fastapi import APIRouter, Query

# Import the RAG agent logic
from app.agents.langgraph_flow import run_rag_agent

# Create a router instance to define endpoints under this module
router = APIRouter()

# Define a GET API endpoint at /ask
@router.get("/ask")
async def ask(question: str = Query(...)):
    # Call the RAG agent to process the input question
    answer = run_rag_agent(question)

    # Return both question and answer in the response
    return {"question": question, "answer": answer}
