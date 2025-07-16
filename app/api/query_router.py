# app/api/query_router.py

from fastapi import APIRouter, Query
from app.agents.langgraph_flow import run_rag_agent
from fastapi import HTTPException
from app.services.postgres_storage import get_history, reset_checkpoint

router = APIRouter()

@router.get("/ask")
async def ask(question: str = Query(...)):
    answer = run_rag_agent(question)
    return {"question": question, "answer": answer}

