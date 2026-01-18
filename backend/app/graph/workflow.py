from langgraph.graph import StateGraph, END
from app.models.state import AgentState

from app.agents.router import router_node, route_decision
from app.agents.clarification import clarification_node
from app.agents.solver import solver_node
from app.agents.synthesizer import synthesizer_node

# 1. Initialize Graph
workflow = StateGraph(AgentState)

# 2. Add Nodes
workflow.add_node("router", router_node)
workflow.add_node("clarification", clarification_node)
workflow.add_node("solver", solver_node)
workflow.add_node("synthesizer", synthesizer_node)

# 3. Define Edges

# Entry point -> Router
workflow.set_entry_point("router")

# Router -> Decision
workflow.add_conditional_edges(
    "router",
    route_decision,
    {
        "clarification": "clarification",
        "solver": "solver",
        "synthesizer": "synthesizer"
    }
)

# Clarification -> Loop or Solver?
# If clarification says "MISSING_INFO", we stop and reply to user (End of turn).
# If "READY", we go to Solver.
def clarification_logic(state: AgentState):
    if state.get("is_ready"):
        return "solver"
    else:
        return END

workflow.add_conditional_edges(
    "clarification",
    clarification_logic,
    {
        "solver": "solver",
        END: END
    }
)

# Solver -> End
workflow.add_edge("solver", END)
workflow.add_edge("synthesizer", END)

from langgraph.checkpoint.memory import MemorySaver

# ... (previous code)

# 4. Compile with Persistence
memory = MemorySaver()
agent_app = workflow.compile(checkpointer=memory)
