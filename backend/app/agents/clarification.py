import json
from typing import Dict, Any
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from app.models.state import AgentState
from app.prompts.templates import CLARIFICATION_PROMPT
from app.config import settings
from app.services.llm import get_llm

def clarification_node(state: AgentState) -> Dict[str, Any]:
    """
    Checks if we have all details needed for booking.
    Uses FULL conversation history for context accumulation.
    """
    messages = state["messages"]
    existing_details = state.get("task_details", {}) or {}
    
    print("--> [CLARIFICATION] Checking for missing info...")
    
    # Build conversation summary from all messages
    conversation_text = ""
    for msg in messages:
        if hasattr(msg, 'type'):
            role = "User" if msg.type == "human" else "Assistant"
            conversation_text += f"{role}: {msg.content}\n"
        elif isinstance(msg, dict):
            role = "User" if msg.get('role') == 'user' else "Assistant"
            conversation_text += f"{role}: {msg.get('content', '')}\n"
    
    # Include previously extracted details in the prompt
    context_prompt = f"""{CLARIFICATION_PROMPT}

PREVIOUS CONVERSATION:
{conversation_text}

PREVIOUSLY EXTRACTED DETAILS (merge with new info):
{json.dumps(existing_details, indent=2) if existing_details else "None yet"}

Analyze the FULL conversation above. Extract ALL details mentioned across ALL messages.
If a field was mentioned earlier in the conversation, include it.
"""
    
    # Construct messages for LLM
    # Use LangChain format
    llm = get_llm()
    
    # Invoke the LLM
    try:
        response = llm.invoke([
            SystemMessage(content=context_prompt),
            HumanMessage(content="Based on the full conversation above, what details do we have and what's missing?")
        ])
        content = response.content
        
        # Clean potential markdown wrapping
        if "```json" in content:
            content = content.replace("```json", "").replace("```", "")
        elif "```" in content:
            content = content.replace("```", "")
            
        content = content.strip()
        
    except Exception as e:
        print(f"[CLARIFICATION] Error calling LLM: {e}")
        content = "{}"
        
    # Parse JSON
    try:
        data = json.loads(content)
    except:
        data = {"status": "MISSING_INFO", "missing_fields": ["generic"], "response_message": "Could you clarify that?"}
    
    # Merge new details with existing
    new_details = data.get("extracted_details", {})
    merged_details = {**existing_details, **{k: v for k, v in new_details.items() if v is not None}}
    
    logs = []
    is_ready = False
    
    if data.get("status") == "READY":
        logs.append("[CLARIFICATION]: All fields present. Proceeding to Solver.")
        is_ready = True
        return {
            "reasoning_logs": logs,
            "task_details": merged_details,
            "is_ready": True,
            "current_step": "clarification"
        }
    else:
        missing = ", ".join(data.get("missing_fields", []))
        logs.append(f"[CLARIFICATION]: Missing {missing}. Asking user: '{data.get('response_message', 'Could you provide more details?')}'")
        return {
            "messages": [AIMessage(content=data.get("response_message", "Could you provide more details?"))],
            "reasoning_logs": logs,
            "missing_info": data.get("missing_fields", []),
            "task_details": merged_details,  # Save partial progress
            "current_step": "clarification",
            "is_ready": False 
        }

