Here is the comprehensive System Architecture & Feature Breakdown for your "AI-Powered Personal Planning & Scheduling Agent," explicitly modeled after the winning RiskWise project from your research document.
This plan transforms a standard "Calendar Bot" into a "Senior Architect-grade" Agentic System.
1. The Core Concept: "Router-Solver" Architecture
Instead of one giant AI trying to do everything, we use the RiskWise Pattern. We split the brain into specialized agents.
The Workflow Visualization
User Request ("Schedule deep work for 2 hours")
       |
       v
[ 1. Router Agent ]  <-- The "Traffic Cop"
       |
       +---> [Is Info Missing?] ----> [ 2. Clarification Agent ]
       |                                      |
       |                             (Asks: "When do you want to start?")
       |                                      |
       |                                      v
       +---> [Is Info Complete?] ---> [ 3. Calendar Solver Agent ]
                                              |
                                     (Checks GCal, Finds Slots, Locks Time)
                                              |
                                              v
                                     [ 4. Response Synthesizer ]
                                              |
                                     ("Scheduled for 10 AM. I moved Lunch to 1 PM.")

2. Feature Mapping: RiskWise vs. Your Scheduler
We will replicate the exact table structure from the RiskWise analysis but adapt the roles for your domain.
| RiskWise Component | Your Scheduler Component | Functionality & Logic |
|---|---|---|
| Assistant Agent (Router) | Intent Router | The Gatekeeper. It analyzes the user's prompt. It does not "do" the work; it classifies the state.
• State A: MISSING_CONTEXT (e.g., "Book a meeting" - with who?)
• State B: EXECUTE_TASK (e.g., "Book Gym at 6 PM")
• State C: QUERY (e.g., "What am I doing today?") |
| Political Risk Agent (Solver) | Clarification Agent | The Investigator. Activated only when State = MISSING_CONTEXT.
It looks at the request, identifies specifically what is missing (Duration? Urgency? Deadline?), and generates a natural language question.
"You mentioned studying for JEE, but is this a mock test (3 hrs) or revision (1 hr)?" |
| Scheduler Agent (Solver) | Calendar Logic Agent | The Calculator. Activated when State = EXECUTE_TASK.
It has Tool Access to the Google Calendar API.
It performs the "Constraint Satisfaction" logic:
1. Fetch existing events.
2. Find gaps of size N.
3. Check user constraints (e.g., "No meetings before 10 AM").
4. Commit the event. |
| Reporting Agent | Explanation Engine | The Communicator. It summarizes the action.
Crucially, it handles the "Reasoning Log" requirement. If it moved a task, it explains why.
"I booked Deep Work at 9 AM. To make this fit, I shifted your 'Review' task to 4 PM." |
3. Key "Winning" Features (The Innovation)
To ensure this is a "Top Contestant" project, we implement the specific architectural wins mentioned in the PDF.
A. The "Chatbot Termination Strategy" (Clarification Loop)
 * The Problem: Most AI agents hallucinate when they don't know something. If you say "Plan my day," they just make up random times.
 * The RiskWise Fix: The PDF mentions a "Chatbot Termination Strategy" to control loops.
 * Your Implementation:
   * The Clarification Agent is a "Hard Stop." The system cannot proceed to the Calendar Solver until the Router certifies that all variables (StartTime, Duration, Priority) are populated.
   * Demo Value: You type "Schedule a meeting." The bot refuses to schedule it and asks "With whom?". Judges love this robustness.
B. Structured "Reasoning Logs" (Transparent AI)
 * The Problem: Users don't trust AI to delete or move their calendar events.
 * The RiskWise Fix: RiskWise provides "Structured Agent Reasoning" logs so users can audit decisions.
 * Your Implementation:
   * On the UI, next to the chat, show a "Thinking..." sidebar.
   * Display the raw logic:
     * [LOG]: Router identified intent: NEW_TASK
     * [LOG]: Clarification Agent: Duration missing. Asking user...
     * [LOG]: User provided "2 hours".
     * [LOG]: Calendar Solver: Found conflict at 2 PM. Shifting candidate slot to 4 PM.
   * This "glass box" approach proves you aren't just wrapping ChatGPT.
C. The "Constraint" Engine (Physics-First Logic)
 * The Problem: AI might book a meeting at 3 AM.
 * The RiskWise Fix: Similar to how Resonant Exoplanets used a "Physics Gatekeeper", you will use a "Logic Gatekeeper."
 * Your Implementation:
   * Inject a "User Preferences" JSON into the System Prompt.
   * {"working_hours": "09:00-18:00", "lunch": "13:00-14:00"}
   * The Calendar Logic Agent treats these as hard constraints (like physical laws). If the AI tries to book lunch at 11 AM, the Solver rejects it before it hits the API.
4. How to Build It (The "Switch Spot" Execution)
Since we are "forking" the concept, here is your path to least resistance:
 * Backend: Use Python with FastAPI.
   * Why? The PDF praises Python for "Agentic Workflows" and specifically mentions Microsoft's Semantic Kernel or LangChain.
   * Use LangGraph (Python) to define the "Router" graph state. It handles the If/Else logic between agents natively.
 * The "Solver" Tool:
   * You don't need to write the calendar algorithm from scratch.
   * Use the Google Calendar API for Python (google-auth-oauthlib, google-api-python-client).
   * Write one function: find_free_slots(duration, start_range, end_range). The AI simply calls this function.
 * Frontend:
   * Keep it simple. Split the screen:
     * Left: Chat Interface.
     * Right: Embed the actual Google Calendar Web View (iframe).
     * Bottom/Side: The "Reasoning Logs" terminal.
   * This saves you from building a complex Calendar UI. You just show the result in the real Google Calendar.