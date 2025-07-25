# app/api/query_router.py

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from app.workflow.workflow import workflow
from app.schemas.rag import RAGState
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api")


@router.get("/ask")
async def ask_question(request: Request, question: str, user_id: str = "default_user", session_id: str = "default_session"):
    logger.info(f"Received question from user '{user_id}' in session '{session_id}': {question}")

    try:
        input_state = RAGState(
            question=question,
            user_id=user_id,
            session_id=session_id
        )

        # Use async workflow invocation
        result: RAGState = await workflow.ainvoke(input_state)

        return JSONResponse({
            "question": question,
            "sub_questions": result.get("sub_questions", []),
            "companies": result.get("companies", []),
            "answers": result.get("answers", []),
            "final_answer": result.get("final_answer", "")
        })

    except Exception as e:
        logger.exception("❌ LangGraph workflow failed")
        return JSONResponse({"error": str(e)}, status_code=500)
