from typing import Dict, Any, Literal
from langchain_core.messages import SystemMessage, HumanMessage
from app.models.state import AgentState
from app.prompts.templates import ROUTER_PROMPT
from app.services.llm import get_llm

def router_node(state: AgentState) -> Dict[str, Any]:
    """
    Classifies the user's intent.
    """
    messages = state["messages"]
    last_message = messages[-1]
    
    # 1. Invoke the LLM
    llm = get_llm()
    
    try:
        # LangChain Usage
        response = llm.invoke([
            SystemMessage(content=ROUTER_PROMPT),
            HumanMessage(content=last_message.content)
        ])
        content = response.content
    except Exception as e:
        print(f"[ROUTER] Error calling LLM: {e}")
        content = "CHITCHAT" # Fallback

    intent = content.strip().upper()
    
    # Fallback/Safety
    valid_intents = ["SCHEDULE_REQUEST", "QUERY", "CHITCHAT"]
    # Simple heuristic to extract intent if the model output implies it but isn't exact
    found_intent = None
    for valid in valid_intents:
        if valid in intent:
            found_intent = valid
            break
            
    if found_intent:
        intent = found_intent
    else:
        intent = "CHITCHAT"
        
    print(f"--> [ROUTER] Classified as: {intent}")
    
    return {
        "current_step": "router",
        "reasoning_logs": [f"[ROUTER]: Analyzing input... Classified as {intent}."]
    }


def route_decision(state: AgentState) -> Literal["clarification", "solver", "synthesizer"]:
    """
    Determines the next node based on the router's logs.
    (In a real implementation, we'd store the intent in state, but parsing logs works for now)
    """
    # Parse the last log to get intent
    last_log = state["reasoning_logs"][-1]
    
    if "SCHEDULE_REQUEST" in last_log:
        return "clarification"
    elif "QUERY" in last_log:
        return "solver" # Query solver logic would go here
    else:
        return "synthesizer" # Just chat back
