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
async def auth_status(user_id: Optional[str] = "default_web_user"):
    """Check if user is authenticated with Google Calendar."""
    return {"authenticated": calendar_service.is_authenticated(user_id)}

@app.get("/auth/login")
async def auth_login(user_id: Optional[str] = "default_web_user"):
    """Get the Google OAuth URL to redirect user to."""
    auth_url = calendar_service.get_auth_url(user_id)
    return {"auth_url": auth_url}

from fastapi.responses import RedirectResponse, HTMLResponse

@app.get("/auth/callback")
async def auth_callback(code: str, state: Optional[str] = "default_web_user"):
    """Handle OAuth callback from Google - redirect back to frontend."""
    success = calendar_service.handle_callback(code, state)
    if success:
        html_content = f"""
        <html>
            <head>
                <title>Auth Success</title>
                <style>
                    body {{ font-family: sans-serif; text-align: center; padding-top: 50px; background-color: #121212; color: #e0e0e0; }}
                    .container {{ max-width: 500px; margin: 0 auto; padding: 20px; border: 1px solid #333; border-radius: 10px; background-color: #1e1e1e; }}
                    h1 {{ color: #4caf50; }}
                    a {{ display: inline-block; margin-top: 20px; padding: 10px 20px; background-color: #2196f3; color: white; text-decoration: none; border-radius: 5px; }}
                </style>
            </head>
            <body>
                <div class="container">
                    <h1>✅ Authentication Successful!</h1>
                    <p>Secure connection established for user ID: {state}</p>
                    <p>You can now close this window and return to the Telegram Bot.</p>
                    <a href="tg://resolve?domain=Kairosengine_bot">Open Telegram</a>
                </div>
            </body>
        </html>
        """
        return HTMLResponse(content=html_content, status_code=200)
    else:
        return HTMLResponse(content="<h1>❌ Authentication Failed</h1><p>Please try again.</p>", status_code=400)

# ==================== SETTINGS ENDPOINTS ====================

class SettingsUpdate(BaseModel):
    llm_provider: Optional[str] = None
    openrouter_api_key: Optional[str] = None
    openrouter_model: Optional[str] = None
    openai_api_key: Optional[str] = None
    openai_model: Optional[str] = None
    google_api_key: Optional[str] = None
    google_model: Optional[str] = None
    google_client_id: Optional[str] = None
    google_client_secret: Optional[str] = None
    working_hours_start: Optional[str] = None
    working_hours_end: Optional[str] = None
    lunch_start: Optional[str] = None
    lunch_end: Optional[str] = None

class TestConnectionRequest(BaseModel):
    provider: str # openrouter, openai, google
    api_key: str
    model: str

@app.get("/settings")
async def get_settings():
    """Get current settings (with masked API keys)."""
    return {
        "llm_provider": settings.LLM_PROVIDER,
        "openrouter_api_key": mask_key(settings.OPENROUTER_API_KEY),
        "openrouter_model": settings.OPENROUTER_MODEL,
        "openai_api_key": mask_key(settings.OPENAI_API_KEY),
        "openai_model": settings.OPENAI_MODEL,
        "google_api_key": mask_key(settings.GOOGLE_API_KEY),
        "google_model": settings.GOOGLE_MODEL,
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
        return "" # Don't show *** if empty
    return key[:4] + "*" * (len(key) - 8) + key[-4:]

@app.post("/settings")
async def update_settings(data: SettingsUpdate):
    """Update settings."""
    if data.llm_provider:
        settings.LLM_PROVIDER = data.llm_provider
    if data.openrouter_api_key and not data.openrouter_api_key.startswith("***"):
        settings.OPENROUTER_API_KEY = data.openrouter_api_key
    if data.openrouter_model:
        settings.OPENROUTER_MODEL = data.openrouter_model
    if data.openai_api_key and not data.openai_api_key.startswith("***"):
        settings.OPENAI_API_KEY = data.openai_api_key
    if data.openai_model:
        settings.OPENAI_MODEL = data.openai_model
    if data.google_api_key and not data.google_api_key.startswith("***"):
        settings.GOOGLE_API_KEY = data.google_api_key
    if data.google_model:
        settings.GOOGLE_MODEL = data.google_model
        
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
    """Test LLM API connection."""
    import time
    from langchain_core.messages import HumanMessage
    
    try:
        # Determine Key
        api_key = data.api_key
        if api_key.startswith("***"):
            # Use stored key
            if data.provider == "openrouter":
                api_key = settings.OPENROUTER_API_KEY
            elif data.provider == "openai":
                api_key = settings.OPENAI_API_KEY
            elif data.provider == "google":
                api_key = settings.GOOGLE_API_KEY
                
        # Instantiate correct client
        llm = None
        if data.provider == "openrouter":
            from langchain_openai import ChatOpenAI
            llm = ChatOpenAI(
                api_key=api_key, 
                base_url="https://openrouter.ai/api/v1",
                model=data.model, 
                temperature=0
            )
        elif data.provider == "openai":
            from langchain_openai import ChatOpenAI
            llm = ChatOpenAI(api_key=api_key, model=data.model, temperature=0)
        elif data.provider == "google":
            from app.services.llm import GoogleGenAIWrapper
            llm = GoogleGenAIWrapper(api_key=api_key, model=data.model, temperature=0)
            
        if not llm:
            return {"success": False, "error": "Invalid provider"}

        start = time.time()
        llm.invoke([HumanMessage(content="Say OK")])
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
