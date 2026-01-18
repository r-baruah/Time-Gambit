from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from pydantic import BaseModel
from typing import Dict, Any, List, Optional
import uvicorn
from langchain_core.messages import HumanMessage

from app.config import settings
from app.graph.workflow import agent_app
from app.services.calendar import calendar_service

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION
)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ChatRequest(BaseModel):
    message: str
    thread_id: Optional[str] = "default_thread"

class AuthCallbackRequest(BaseModel):
    code: str

@app.get("/health")
async def health_check():
    return {"status": "ok", "app": settings.APP_NAME}

# ==================== AUTH ENDPOINTS ====================

@app.get("/auth/status")
async def auth_status():
    """Check if user is authenticated with Google Calendar."""
    return {"authenticated": calendar_service.is_authenticated()}

@app.get("/auth/login")
async def auth_login():
    """Get the Google OAuth URL to redirect user to."""
    auth_url = calendar_service.get_auth_url()
    return {"auth_url": auth_url}

@app.get("/auth/callback")
async def auth_callback(code: str):
    """Handle OAuth callback from Google - redirect back to frontend."""
    success = calendar_service.handle_callback(code)
    if success:
        # Redirect to frontend with success
        return RedirectResponse(url="http://localhost:3000?auth=success")
    else:
        return RedirectResponse(url="http://localhost:3000?auth=failed")

# ==================== SETTINGS ENDPOINTS ====================

class SettingsUpdate(BaseModel):
    openrouter_api_key: Optional[str] = None
    openrouter_model: Optional[str] = None
    openai_api_key: Optional[str] = None
    google_client_id: Optional[str] = None
    google_client_secret: Optional[str] = None
    working_hours_start: Optional[str] = None
    working_hours_end: Optional[str] = None
    lunch_start: Optional[str] = None
    lunch_end: Optional[str] = None

class TestConnectionRequest(BaseModel):
    api_key: str
    model: str

@app.get("/settings")
async def get_settings():
    """Get current settings (with masked API keys)."""
    return {
        "openrouter_api_key": mask_key(settings.OPENROUTER_API_KEY),
        "openrouter_model": settings.OPENROUTER_MODEL,
        "openai_api_key": mask_key(settings.OPENAI_API_KEY),
        "google_client_id": settings.GOOGLE_CLIENT_ID,
        "google_client_secret": mask_key(settings.GOOGLE_CLIENT_SECRET),
        "working_hours_start": settings.USER_WORKING_HOURS_START,
        "working_hours_end": settings.USER_WORKING_HOURS_END,
        "lunch_start": settings.USER_LUNCH_START,
        "lunch_end": settings.USER_LUNCH_END,
    }

def mask_key(key: str) -> str:
    """Mask API key for display."""
    if not key or len(key) < 8:
        return "***"
    return key[:4] + "*" * (len(key) - 8) + key[-4:]

@app.post("/settings")
async def update_settings(data: SettingsUpdate):
    """Update settings. Note: In production, this should persist to .env or database."""
    import os
    
    # Update in-memory settings (for demo - in production you'd write to .env)
    if data.openrouter_api_key and not data.openrouter_api_key.startswith("***"):
        settings.OPENROUTER_API_KEY = data.openrouter_api_key
    if data.openrouter_model:
        settings.OPENROUTER_MODEL = data.openrouter_model
    if data.openai_api_key and not data.openai_api_key.startswith("***"):
        settings.OPENAI_API_KEY = data.openai_api_key
    if data.working_hours_start:
        settings.USER_WORKING_HOURS_START = data.working_hours_start
    if data.working_hours_end:
        settings.USER_WORKING_HOURS_END = data.working_hours_end
    if data.lunch_start:
        settings.USER_LUNCH_START = data.lunch_start
    if data.lunch_end:
        settings.USER_LUNCH_END = data.lunch_end
        
    return {"status": "ok"}

@app.post("/settings/test")
async def test_connection(data: TestConnectionRequest):
    """Test OpenRouter API connection."""
    import time
    try:
        from openrouter import OpenRouter
        
        api_key = data.api_key if not data.api_key.startswith("***") else settings.OPENROUTER_API_KEY
        
        client = OpenRouter(api_key=api_key)
        start = time.time()
        response = client.chat.send(
            model=data.model,
            messages=[{"role": "user", "content": "Say OK"}],
            temperature=0
        )
        latency = int((time.time() - start) * 1000)
        
        return {"success": True, "latency": latency}
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.post("/chat")
async def chat_endpoint(request: ChatRequest):
    """
    Main endpoint triggering the LangGraph workflow.
    """
    user_message = request.message
    thread_id = request.thread_id or "default_thread"
    
    config = {"configurable": {"thread_id": thread_id}}
    
    # Run the graph
    # We pass ONLY the new message. The graph loads history from MemorySaver.
    input_update = {"messages": [HumanMessage(content=user_message)]}
    
    result = await agent_app.ainvoke(input_update, config=config)
    
    # Transform result for Frontend
    # result["messages"] contains the FULL history now.
    
    final_messages = []
    for m in result["messages"]:
        if hasattr(m, "content"):
            role = "user" if m.type == "human" else "assistant"
            final_messages.append({"role": role, "content": m.content})
        else:
            final_messages.append(m)
            
    return {
        "messages": final_messages,
        "current_step": result.get("current_step", "done"),
        "reasoning_logs": result.get("reasoning_logs", [])
    }

if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
