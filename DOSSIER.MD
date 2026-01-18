Here is the complete Project Dossier. You can copy and paste this entire block directly into a file named CONTEXT.md or DOSSIER.md in your project root.
This file provides your AI Developer Agent (e.g., Cursor, Windsurf, or ChatGPT) with the Problem Statement, the Winning Architecture, and the Technical Specifications needed to build the project without needing to "guess."
PROJECT DOSSIER: AI-Powered Personal Planning & Scheduling Agent
1. The Core Objective
To build a "Top Contestant" quality Agentic AI system that manages a user's Google Calendar. The system must move beyond simple "chatbot" interactions by implementing a robust Router-Solver Architecture (inspired by the Microsoft "RiskWise" winning project). It must intelligently reason about time, ask clarification questions when data is missing, and execute verified actions.
2. The Problem Statement (Source of Truth)
From the official Hackathon Problem Statement:
Project Goal:
Help users intelligently plan their day or week by reasoning over tasks, urgency, time requirements, and personal constraints, and automatically scheduling them into the user’s Google Calendar.
Functional Requirements:
 * Natural Language Input: Accept tasks like "Plan my study session" with optional details (deadlines, priorities, effort).
 * Clarification Loop: Ask targeted clarification questions to infer missing details (urgency, duration, etc.) before acting.
 * Logic & Reasoning: Reason about task importance and deadlines to determine optimal execution order.
 * Calendar Integration: Integrate with Google Calendar to read events and write new ones without overlaps.
 * Constraints: Respect user-defined working hours, lunch periods, and breaks.
 * Adaptability: Dynamically reschedule tasks when constraints change and explain the rescheduling decisions.
3. The "Winning" Architecture: Router-Solver Pattern
Reference Architecture: "RiskWise" (Microsoft AI Agents Hackathon Winner)
We are rejecting the monolithic LLM approach. We will implement a Multi-Agent State Graph (Router-Solver Pattern).
Component Mapping
| RiskWise Role | Our Project Role | Responsibility |
|---|---|---|
| Assistant Agent (Router) | Intent Router | The Gatekeeper. Classifies user input into a specific state. It does NOT schedule. It only decides who handles the request. |
| Political Risk Agent | Clarification Agent | The Investigator. Activated if the Router detects MISSING_INFO. It generates specific questions to gather variables (Duration, Deadline, Urgency). |
| Scheduler Agent | Calendar Solver | The Doer. Activated only when state is READY. It interacts with the Google Calendar API. It solves the "Time Slot" math problem using constraints. |
| Reporting Agent | Synthesizer | The Voice. Formats the final confirmation and explains the logic (e.g., "I moved X to fit Y"). |
The Control Flow (The "Chatbot Termination Strategy")
To prevent hallucinations, we enforce a strict Termination Strategy:
 * Input: User says "Book a meeting."
 * Router: Detects missing duration and attendees.
 * Route: Sends to Clarification Agent.
 * Output: Agent asks "Who is the meeting with and for how long?"
 * STOP: The system terminates execution and waits for user input. It does not attempt to guess the time.
4. Technical Specifications
Tech Stack
 * Language: Python 3.10+ (Preferred for Agentic Workflows).
 * Orchestration: LangGraph (Perfect for stateful Router-Solver flows).
 * Backend: FastAPI (Expose the agent as a REST endpoint).
 * LLM: OpenAI GPT-4o or equivalent (via LangChain).
 * Integration: Google Calendar API (OAuth 2.0).
Data Structures
The Agent State (Shared Memory):
class AgentState(TypedDict):
    messages: List[BaseMessage]
    current_step: str         # "router", "clarification", "solver"
    task_details: Optional[Dict]  # { "title": str, "duration": int, "deadline": str }
    missing_info: List[str]   # ["duration", "priority"]
    calendar_events: List[Dict]   # Context from GCal
    reasoning_logs: List[str] # For the "Explainability" requirement
    Key "Winning" Features to Implement
 * Reasoning Logs:
   * The UI must display "Thought Bubbles" or a log terminal showing the agent's internal steps (e.g., [LOG]: Found conflict at 2 PM. Trying 4 PM...).
 * Constraint Injection:
   * Inject a "User Manifesto" into the System Prompt:
   * CONSTRAINTS: { "working_hours": "09:00-17:00", "lunch": "13:00-14:00" }
   * The Calendar Solver must treat these as "Physical Laws" (inviolable).
5. Implementation Roadmap (For the AI Dev)
Phase 1: The Skeleton (Router)
 * Setup FastAPI + LangGraph.
 * Build the Router node that categorizes input into SCHEDULE_REQUEST, QUERY, or CHITCHAT.
Phase 2: The Logic (Clarification)
 * Build the Clarification node.
 * Implement the prompt logic: "If duration is missing, ask the user."
 * Goal: The agent should refuse to schedule vague tasks.
Phase 3: The Tool (Calendar)
 * Implement GoogleCalendarService.
 * Build find_available_slots(duration, range) function.
 * Connect the Calendar Solver node to this service.
Phase 4: The Interface (Transparency)
 * Build a simple UI (Streamlit or React) that shows the Reasoning Logs side-by-side with the Chat.