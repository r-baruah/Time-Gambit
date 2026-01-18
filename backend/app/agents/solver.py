from datetime import datetime, timedelta
from typing import Dict, Any, Optional, Tuple
from langchain_core.messages import AIMessage
from app.models.state import AgentState
from app.services.calendar import calendar_service
from app.config import settings
import re

def parse_date_from_text(text: str, reference_date: datetime = None) -> Optional[datetime]:
    """Parse natural language date into datetime object."""
    if reference_date is None:
        reference_date = datetime.now()
    
    text_lower = text.lower()
    
    # Handle "24th", "25th" etc (day of current/next month)
    day_match = re.search(r'(\d{1,2})(?:st|nd|rd|th)', text_lower)
    if day_match:
        day = int(day_match.group(1))
        target_date = reference_date.replace(day=day, hour=9, minute=0, second=0, microsecond=0)
        if target_date < reference_date:
            # Move to next month
            if reference_date.month == 12:
                target_date = target_date.replace(year=reference_date.year + 1, month=1)
            else:
                target_date = target_date.replace(month=reference_date.month + 1)
        return target_date
    
    # Handle "tomorrow"
    if "tomorrow" in text_lower:
        return (reference_date + timedelta(days=1)).replace(hour=9, minute=0, second=0, microsecond=0)
    
    # Handle "next week"
    if "next week" in text_lower:
        return (reference_date + timedelta(days=7)).replace(hour=9, minute=0, second=0, microsecond=0)
    
    # Handle ISO format dates
    iso_match = re.search(r'(\d{4}-\d{2}-\d{2})', text)
    if iso_match:
        return datetime.fromisoformat(iso_match.group(1)).replace(hour=9, minute=0, second=0, microsecond=0)
    
    return None

def parse_duration_from_text(text: str) -> timedelta:
    """Parse duration from text, default to 1 hour."""
    text_lower = text.lower() if text else ""
    
    # Handle "full day" or "all day"
    if "full day" in text_lower or "all day" in text_lower:
        return timedelta(hours=8)
    
    # Handle hours
    hour_match = re.search(r'(\d+)\s*(?:hour|hr|h)', text_lower)
    if hour_match:
        return timedelta(hours=int(hour_match.group(1)))
    
    # Handle minutes
    min_match = re.search(r'(\d+)\s*(?:minute|min|m)', text_lower)
    if min_match:
        return timedelta(minutes=int(min_match.group(1)))
    
    # Default
    return timedelta(hours=1)

def get_working_hours() -> Tuple[int, int, int, int]:
    """Get working hours from settings."""
    start_parts = settings.USER_WORKING_HOURS_START.split(":")
    end_parts = settings.USER_WORKING_HOURS_END.split(":")
    lunch_start_parts = settings.USER_LUNCH_START.split(":")
    lunch_end_parts = settings.USER_LUNCH_END.split(":")
    
    return (
        int(start_parts[0]),  # work_start_hour
        int(end_parts[0]),    # work_end_hour
        int(lunch_start_parts[0]),  # lunch_start_hour
        int(lunch_end_parts[0])     # lunch_end_hour
    )

def find_available_slot(target_date: datetime, duration: timedelta, existing_events: list) -> Optional[Tuple[datetime, datetime]]:
    """Find an available slot on the target date respecting constraints."""
    work_start, work_end, lunch_start, lunch_end = get_working_hours()
    
    # Generate candidate slots (every 30 min during working hours, excluding lunch)
    candidate_start = target_date.replace(hour=work_start, minute=0, second=0, microsecond=0)
    candidate_end = target_date.replace(hour=work_end, minute=0, second=0, microsecond=0)
    
    current = candidate_start
    while current + duration <= candidate_end:
        slot_end = current + duration
        
        # Skip lunch hours
        if current.hour >= lunch_start and current.hour < lunch_end:
            current = current.replace(hour=lunch_end, minute=0)
            continue
        
        # Check if slot overlaps with lunch
        if current.hour < lunch_start and slot_end.hour > lunch_start:
            current = current.replace(hour=lunch_end, minute=0)
            continue
        
        # Check against existing events
        is_free = True
        for event in existing_events:
            event_start = event.get('start', {}).get('dateTime', event.get('start', {}).get('date'))
            event_end = event.get('end', {}).get('dateTime', event.get('end', {}).get('date'))
            
            if event_start and event_end:
                try:
                    ev_start = datetime.fromisoformat(event_start.replace('Z', '+00:00')).replace(tzinfo=None)
                    ev_end = datetime.fromisoformat(event_end.replace('Z', '+00:00')).replace(tzinfo=None)
                    
                    # Check overlap
                    if not (slot_end <= ev_start or current >= ev_end):
                        is_free = False
                        break
                except:
                    pass
        
        if is_free:
            return (current, slot_end)
        
        current += timedelta(minutes=30)
    
    return None

from langchain_core.runnables import RunnableConfig

def solver_node(state: AgentState, config: RunnableConfig) -> Dict[str, Any]:
    """
    Enhanced Calendar Solver with:
    - Natural language date parsing
    - Working hours constraints
    - Lunch break respect
    - Auto-scheduling to Google Calendar
    """
    print("--> [SOLVER] Resolving constraints...")
    
    # Extract user_id from thread_id
    user_id = config.get("configurable", {}).get("thread_id", "default_web_user")
    
    # 0. Check for QUERY intent
    
    is_query = False
    for log in reversed(state.get("reasoning_logs", [])):
        if "Classified as QUERY" in log:
            is_query = True
            break
        if "Classified as" in log: # Stop at the most recent classification
            break
            
    if is_query:
        print(f"--> [SOLVER] detected QUERY mode for {user_id}.")
        events = calendar_service.list_events(user_id=user_id, max_results=5)
        if not events:
             response_msg = "Your calendar is clear for the next few upcoming events."
        else:
            response_msg = "**Upcoming Events:**\n"
            for event in events:
                start = event.get('start', {}).get('dateTime', event.get('start', {}).get('date'))
                # Simple formatting
                try:
                    dt = datetime.fromisoformat(start.replace('Z', '+00:00'))
                    date_str = dt.strftime("%a, %b %d at %I:%M %p")
                except:
                    date_str = start
                
                response_msg += f"• **{event.get('summary', 'Untitled')}** ({date_str})\n"
                
        return {
            "reasoning_logs": ["[SOLVER]: Executed Read-Only Query."],
            "messages": [AIMessage(content=response_msg)],
            "current_step": "solver"
        }

    new_logs = []
    new_logs.append(f"[SOLVER]: Connecting to Google Calendar API for {user_id}...")
    
    try:
        # Get existing events for the week
        events = calendar_service.list_events(user_id=user_id, max_results=10)
        event_summaries = [e.get('summary', 'Untitled') for e in events]
        if event_summaries:
            new_logs.append(f"[SOLVER]: Found {len(events)} upcoming events: {', '.join(event_summaries[:3])}...")
        else:
            new_logs.append("[SOLVER]: No upcoming events found.")
        
        # Get task details from state
        task = state.get("task_details", {})
        messages = state.get("messages", [])
        
        # Try to extract info from the last user message if task_details is empty
        last_user_msg = ""
        for msg in reversed(messages):
            if hasattr(msg, 'type') and msg.type == "human":
                last_user_msg = msg.content
                break
            elif isinstance(msg, dict) and msg.get('role') == 'user':
                last_user_msg = msg.get('content', '')
                break
        
        # Parse the date
        target_date = None
        if task.get('date'):
            target_date = parse_date_from_text(str(task.get('date')))
        if not target_date and last_user_msg:
            target_date = parse_date_from_text(last_user_msg)
        if not target_date:
            target_date = datetime.now() + timedelta(days=1)
            new_logs.append("[SOLVER]: No specific date found, using tomorrow.")
        else:
            new_logs.append(f"[SOLVER]: Targeting date: {target_date.strftime('%B %d, %Y')}")
        
        # Parse duration
        duration_str = task.get('duration', '') or ''
        duration = parse_duration_from_text(duration_str)
        if not duration_str:
            duration = timedelta(hours=1)
            new_logs.append("[SOLVER]: Duration not specified, defaulting to 1 hour.")
        else:
            new_logs.append(f"[SOLVER]: Duration: {duration}")
        
        # Get title
        title = task.get('title', 'Scheduled Task')
        if not title or title == 'Scheduled Task':
            title = last_user_msg.split(" on ")[0] if " on " in last_user_msg else last_user_msg[:50]
            title = title.strip().title()
        
        # Find available slot
        work_start, work_end, lunch_start, lunch_end = get_working_hours()
        new_logs.append(f"[SOLVER]: Checking availability (Working: {work_start}:00-{work_end}:00, Lunch: {lunch_start}:00-{lunch_end}:00)")
        
        slot = find_available_slot(target_date, duration, events)
        
        if slot:
            start_time, end_time = slot
            new_logs.append(f"[SOLVER]: Found FREE slot: {start_time.strftime('%I:%M %p')} - {end_time.strftime('%I:%M %p')}")
            
            # AUTO-SCHEDULE: Create the event
            new_event = calendar_service.create_event(
                user_id=user_id,
                summary=title,
                start_time=start_time.isoformat(),
                end_time=end_time.isoformat(),
                description=f"Scheduled by AI Planning Agent. Priority: {task.get('priority', 'medium')}"
            )
            
            new_logs.append(f"[SOLVER]: ✅ Event '{title}' SCHEDULED successfully!")
            
            response_msg = f"✅ Done! I've scheduled **'{title}'** for **{start_time.strftime('%B %d, %Y')}** from **{start_time.strftime('%I:%M %p')}** to **{end_time.strftime('%I:%M %p')}**. It's now on your Google Calendar!"
        else:
            new_logs.append(f"[SOLVER]: ❌ No available slot found on {target_date.strftime('%B %d')}.")
            response_msg = f"I couldn't find a free slot on {target_date.strftime('%B %d')} within your working hours. Would you like me to check another day?"
            
    except Exception as e:
        new_logs.append(f"[SOLVER]: Error: {str(e)}")
        response_msg = f"I encountered an error while scheduling: {str(e)}"

    return {
        "reasoning_logs": new_logs,
        "messages": [AIMessage(content=response_msg)],
        "current_step": "solver"
    }

