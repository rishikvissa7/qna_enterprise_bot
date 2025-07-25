import re
import json
import logging
from langgraph.graph import StateGraph
from app.db.db import SessionLocal
from app.services.postgres_storage import (
    get_session_history,
    save_session_checkpoint,
    save_turn,
)
from app.tools.tools import qdrant_search_tool, stock_price_tool, web_search_tool
from app.schemas.rag import RAGState
from litellm import completion

logger = logging.getLogger(__name__)


async def company_selector_node(state: RAGState) -> RAGState:
    logger.info("[LangGraph] 🧠 Running company_selector_node")

    session_id = state.get("session_id")
    user_id = state.get("user_id", "default_user")
    question = state.get("question", "")

    prev_state = get_session_history(session_id, user_id) if session_id else {}
    last_company = (
        prev_state.get("companies", [])[-1]
        if prev_state and prev_state.get("companies")
        else None
    )

    if last_company and re.search(r"\b(that|this|the)\s+company\b", question, re.IGNORECASE):
        question = re.sub(
            r"\b(that|this|the)\s+company\b",
            last_company,
            question,
            flags=re.IGNORECASE
        )
        logger.info(f"🔁 Injected last_company: {last_company}")


    system_prompt = (
        "You are an intelligent assistant that breaks down a multi-question user input. "
        "Your job is to extract a list of {question, company} pairs in JSON format.\n\n"
        "For example:\n"
        "Input: 'Tell me the stock price of Amazon and latest news about Qualcomm.'\n"
        "Output: [\n"
        "  {\"question\": \"What is the stock price of Amazon?\", \"company\": \"Amazon\"},\n"
        "  {\"question\": \"What are the latest news about Qualcomm?\", \"company\": \"Qualcomm\"}\n"
        "]\n\n"
        "Only respond with a valid JSON list. Do not include extra text or explanation."
    )

    logger.info(f"Final question sent to Gemini: {question}")

    try:
        response = completion(
            model="gemini/gemini-2.5-flash",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": question},
            ],
        )

        raw = response.choices[0].message.content.strip()
        logger.info(f"🔍 Gemini raw response: {raw}")

        cleaned = re.sub(r"^```(?:json)?\n|\n```$", "", raw).strip()

        try:
            parsed = json.loads(cleaned)
        except json.JSONDecodeError as je:
            logger.warning(f"❗ JSON decode failed: {je} | Retrying after fix attempt...")
            try:
                cleaned = cleaned.replace("'", '"')
                parsed = json.loads(cleaned)
            except Exception as e:
                logger.error(f"🛑 Final parse failure: {e}")
                raise ValueError("Gemini failed to extract sub-questions and companies.")

        sub_questions = [q["question"] for q in parsed]
        companies = [q.get("company") or last_company or "" for q in parsed]

        if not any(companies) and last_company:
            companies = [last_company] * len(sub_questions)
            sub_questions = [
                sq if last_company.lower() in sq.lower() else f"{sq} about {last_company}"
                for sq in sub_questions
            ]

        for sub_q in sub_questions:
            await save_turn(user_id=user_id, role="user", content=sub_q, session_id=session_id)

        state["question"] = question
        state["sub_questions"] = sub_questions
        state["companies"] = companies

        if session_id:
            save_session_checkpoint(session_id, state.dict(), user_id=user_id)

        return state

    except Exception as e:
        logger.error(f"❌ Error in company_selector_node: {e}")
        raise


async def tool_selector_node(state: RAGState) -> RAGState:
    logger.info("[LangGraph] 🛠️ Running tool_selector_node")

    session_id = state.get("session_id")
    user_id = state.get("user_id", "default_user")

    prev_state = get_session_history(session_id) if session_id else {}
    last_company = (
        prev_state.get("companies", [])[-1]
        if prev_state and prev_state.get("companies")
        else None
    )

    state["tools"] = []
    state["answers"] = []

    db = SessionLocal()
    try:
        for sub_q, company in zip(state.get("sub_questions", []), state.get("companies", [])):
            effective_company = company or last_company or ""

            tool = "qdrant_search"
            answer = "No answer"

            try:
                if any(word in sub_q.lower() for word in ["stock", "share", "price", "market cap", "finance", "earnings"]):
                    tool = "stock_details"
                else:
                    tool = "qdrant_search"
            except Exception as e:
                logger.warning(f"[ToolSelector] Heuristic failed for '{sub_q}': {e}")

            logger.info(f"[ToolSelector] Q: '{sub_q}' | Company: '{effective_company}' | Tool: '{tool}'")
            state["tools"].append(tool)

            try:
                if tool == "qdrant_search":
                    answer = qdrant_search_tool.invoke({"question": sub_q, "company": effective_company})
                    if not answer or "No results" in answer:
                        logger.info(f"[Fallback] Web search for: {sub_q}")
                        answer = web_search_tool.invoke({"question": sub_q, "company": effective_company})
                elif tool == "stock_details":
                    answer = stock_price_tool.invoke({"company": effective_company})
                elif tool == "web_search":
                    answer = web_search_tool.invoke({"question": sub_q, "company": effective_company})
                else:
                    answer = "Tool not recognized"
            except Exception as e:
                logger.error(f"[ToolSelector] Tool execution error: {e}")
                answer = f"Error from {tool}: {e}"

            state["answers"].append(answer)
            await save_turn(user_id=user_id, role="assistant", content=answer, session_id=session_id)

        if session_id:
            save_session_checkpoint(session_id, state.dict(), user_id=user_id)

        return state

    finally:
        db.close()


async def end_node(state: RAGState) -> RAGState:
    logger.info("[LangGraph] ✅ Reached end_node")
    session_id = state.get("session_id")
    state["final_answer"] = "\n\n".join(state.get("answers", []))
    if session_id:
        save_session_checkpoint(session_id, state.dict(), user_id=state.get("user_id", "default_user"))
    return state


def get_graph():
    builder = StateGraph(state_schema=RAGState)
    builder.add_node("company_selector", company_selector_node)
    builder.add_node("tool_selector", tool_selector_node)
    builder.add_node("end", end_node)

    builder.set_entry_point("company_selector")
    builder.add_edge("company_selector", "tool_selector")
    builder.add_edge("tool_selector", "end")

    return builder.compile()


workflow = get_graph()
