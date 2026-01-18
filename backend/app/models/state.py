from typing import Annotated, Dict, List, Optional, TypedDict
from langchain_core.messages import BaseMessage
import operator

class AgentState(TypedDict):
    # The messages in the conversation
    messages: Annotated[List[BaseMessage], operator.add]
    
    # The current step in the workflow: "router", "clarification", "solver", "synthesizer"
    current_step: str
    
    # Details of the task being scheduled
    task_details: Optional[Dict]  # { "title": str, "duration": int, "deadline": str, "start_time": str }
    
    # Information currently missing from the user request
    missing_info: List[str]
    
    # Context fetched from Google Calendar
    calendar_events: List[Dict]
    
    # Reasoning logs for the "Explainability" requirement
    # Annotated with operator.add so we can easily append to it across nodes
    reasoning_logs: Annotated[List[str], operator.add]
    
    # Whether the task is ready for scheduling
    is_ready: bool
