from typing import Dict, Any
from langchain_core.messages import AIMessage
from app.models.state import AgentState

def synthesizer_node(state: AgentState) -> Dict[str, Any]:
    """
    Simple node to just reply if it's chitchat or if we need to wrap up.
    """
    logs = state["reasoning_logs"]
    last_log = logs[-1]
    
    response_text = "I'm listening."
    
    if "CHITCHAT" in last_log:
        response_text = "Hello! I am your Agentic Scheduler. I can allow you to schedule meetings effectively."
        
    return {
        "messages": [AIMessage(content=response_text)],
        "current_step": "synthesizer",
        "reasoning_logs": ["[SYNTHESIZER]: Generated response."]
    }
