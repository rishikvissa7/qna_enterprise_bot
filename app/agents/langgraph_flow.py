from app.services.litellm_llm import get_litellm_chat_model

from app.services.postgres_storage import get_history, save_turn, save_checkpoint, load_checkpoint

from app.schemas.rag import RAGState

llm = get_litellm_chat_model()

from langchain.agents import initialize_agent, Tool
from langchain.agents.agent_types import AgentType
from langgraph.graph import StateGraph, END
from app.schemas.rag import RAGState
from app.tools.rag_tools import (
    google_rag_tool, apple_rag_tool,
    amazon_rag_tool, tesla_rag_tool, tcs_rag_tool
)

tools = [
    Tool.from_function(google_rag_tool, name="google_rag_tool", description="Search Google collection"),
    Tool.from_function(apple_rag_tool, name="apple_rag_tool", description="Search Apple collection"),
    Tool.from_function(amazon_rag_tool, name="amazon_rag_tool", description="Search Amazon collection"),
    Tool.from_function(tesla_rag_tool, name="tesla_rag_tool", description="Search Tesla collection"),
    Tool.from_function(tcs_rag_tool, name="tcs_rag_tool", description="Search TCS collection"),
]

rag_agent = initialize_agent(
    tools=tools,
    llm=llm,
    agent=AgentType.OPENAI_FUNCTIONS,
    verbose=True
)

def agent_node(state):
    try:
        question = state["question"]
        response = rag_agent.invoke({"input": question})
        return {"question": question, "response": response}
    except Exception as e:
        return {"question": state.get("question", ""), "response": f"Agent Error: {str(e)}"}


def end_node(state: RAGState) -> RAGState:
    return {"final_answer": state["response"]}

def get_rag_graph():
    builder = StateGraph(state_schema=RAGState)
    builder.add_node("main_agent", agent_node)
    builder.set_entry_point("main_agent")
    builder.add_edge("main_agent", "end")
    builder.add_node("end", end_node)
    return builder.compile()

# app/agents/langgraph_flow.py


def build_context(history: list) -> str:
    return "\n".join(f"{turn['role'].capitalize()}: {turn['content']}" for turn in history)

def run_rag_agent(question: str) -> str:
    user_id = "default_user"  # 👤 Only one user — hardcoded

    # Get previous conversation history
    history = get_history(user_id)
    context = build_context(history)

    # Include past context if any
    full_input = f"{context}\nUser: {question}" if context else question

    # Load checkpoint if exists
    checkpoint_state = load_checkpoint(user_id)
    if checkpoint_state:
        state = checkpoint_state
        state["question"] = full_input
    else:
        state = {"question": full_input}

    # Run LangGraph
    graph = get_rag_graph()
    result = graph.invoke(state)

    # Extract clean output (only answer)
    raw_answer = result.get("final_answer") or result.get("response")
    if isinstance(raw_answer, dict):
        answer = raw_answer.get("output", str(raw_answer))
    else:
        answer = raw_answer

    # Save clean question & answer only
    save_turn(user_id, "user", question)
    save_turn(user_id, "assistant", answer)

    # Save checkpoint
    save_checkpoint(user_id, result)

    return answer
