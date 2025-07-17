# app/agents/langgraph_flow.py
from app.services.litellm_llm import get_litellm_chat_model  # Custom LLM wrapper
from app.services.postgres_storage import get_history, save_turn, save_checkpoint, load_checkpoint  # Database functions
from app.schemas.rag import RAGState  # Pydantic schema to define RAG state

from langchain.agents import initialize_agent, Tool  # Agent setup and tool abstraction
from langchain.agents.agent_types import AgentType  # Available agent types (e.g., OpenAI functions)
from langgraph.graph import StateGraph, END  # LangGraph for defining AI workflows

# Import specific RAG tools
from app.tools.rag_tools import (
    google_rag_tool, apple_rag_tool,
    amazon_rag_tool, tesla_rag_tool, tcs_rag_tool
)


# STEP 1: Initialize the LLM
# Get a language model instance using LiteLLM abstraction
llm = get_litellm_chat_model()



# STEP 2: Define Available Tools
# Tools represent functions the agent can call a sepecific company collection
tools = [
    Tool.from_function(google_rag_tool, name="google_rag_tool", description="Search Google collection"),
    Tool.from_function(apple_rag_tool, name="apple_rag_tool", description="Search Apple collection"),
    Tool.from_function(amazon_rag_tool, name="amazon_rag_tool", description="Search Amazon collection"),
    Tool.from_function(tesla_rag_tool, name="tesla_rag_tool", description="Search Tesla collection"),
    Tool.from_function(tcs_rag_tool, name="tcs_rag_tool", description="Search TCS collection"),
]


# STEP 3: Initialize Agent
# Create an agent that can decide which tool to use based on user input
rag_agent = initialize_agent(
    tools=tools,  # List of tools it can use
    llm=llm,  # The language model
    agent=AgentType.OPENAI_FUNCTIONS,  # Agent type
    verbose=True  # Logs execution details for debugging
)


# STEP 4: Define Graph Nodes
# This node processes the user's question through the agent and returns the response
def agent_node(state):
    try:
        question = state["question"]
        response = rag_agent.invoke({"input": question})  # Run agent with the question
        return {"question": question, "response": response}  # Pass forward both
    except Exception as e:
        # Catch and return error response if agent fails
        return {"question": state.get("question", ""), "response": f"Agent Error: {str(e)}"}

# This node represents the end of the LangGraph pipeline
def end_node(state: RAGState) -> RAGState:
    # Store the final output for the user
    return {"final_answer": state["response"]}



# STEP 5: Build LangGraph Workflow
def get_rag_graph():
    builder = StateGraph(state_schema=RAGState)  # Graph expects states matching RAGState schema

    builder.add_node("main_agent", agent_node)  # Main processing node
    builder.set_entry_point("main_agent")  # Start here
    builder.add_edge("main_agent", "end")  # Link to final node
    builder.add_node("end", end_node)  # Final output node

    return builder.compile()  # Compile into a runnable graph



# STEP 6: Helper to Build Context from History

def build_context(history: list) -> str:
    # Convert history into a readable conversation string
    return "\n".join(f"{turn['role'].capitalize()}: {turn['content']}" for turn in history)



# STEP 7: Entry Function to Handle Question-Answering

def run_rag_agent(question: str) -> str:
    user_id = "default_user"

    # Step 1: Load conversation history for context
    history = get_history(user_id)
    context = build_context(history)

    # Step 2: Combine past context with new question
    full_input = f"{context}\nUser: {question}" if context else question

    # Step 3: Try to load checkpointed agent state (for multi-turn conversations)
    checkpoint_state = load_checkpoint(user_id)
    if checkpoint_state:
        state = checkpoint_state
        state["question"] = full_input  # Update with new input
    else:
        state = {"question": full_input}

    # Step 4: Run the LangGraph RAG pipeline
    graph = get_rag_graph()
    result = graph.invoke(state)

    # Step 5: Extract final answer from the graph output
    raw_answer = result.get("final_answer") or result.get("response")

    # Clean up response in case it’s a dictionary (agent tools may return structured outputs)
    if isinstance(raw_answer, dict):
        answer = raw_answer.get("output", str(raw_answer))
    else:
        answer = raw_answer

    # Step 6: Save the question and answer to conversation history
    save_turn(user_id, "user", question)
    save_turn(user_id, "assistant", answer)

    # Step 7: Save the agent state checkpoint
    save_checkpoint(user_id, result)

    # Step 8: Return the answer
    return answer
