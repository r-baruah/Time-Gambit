import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler
import httpx
from .auth import is_authenticated, generate_login_link
from .config import BACKEND_API_URL

# States for ConversationHandler (if needed later)
CHOOSING = 0

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Entry point: /start
    Checks authentication status.
    """
    user = update.effective_user
    chat_id = update.effective_chat.id
    
    if await is_authenticated(chat_id):
        await update.message.reply_text(
            f"Hello {user.first_name}! \n\n"
            "Systems Online. 🟢\n"
            "I am ready to manage your schedule. What would you like to do?\n"
            "Try: 'Schedule a meeting with Nilesh on Tuesday'"
        )
    else:
        # Not authenticated - Show Login Link as text (Telegram doesn't allow localhost in buttons)
        login_url = generate_login_link(chat_id, BACKEND_API_URL)
        
        await update.message.reply_text(
            "🛑 **Authentication Required**\n\n"
            "I cannot access your calendar without your permission.\n\n"
            "**Step 1:** Open this link in your browser:\n"
            f"`{login_url}`\n\n"
            "**Step 2:** Sign in with Google and grant calendar access.\n\n"
            "**Step 3:** Return here and type /start to activate.",
            parse_mode="Markdown"
        )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "**Usage:**\n"
        "/start - Initialize connection\n"
        "/settings - Configure API keys\n"
        "Otherwise, just talk to me naturally.",
        parse_mode="Markdown"
    )

async def settings(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    BYOK (Bring Your Own Key) Flow
    """
    # For the hackathon, we can make this a simple toggle or info message
    # since storing keys securely via chat is tricky without a DB.
    await update.message.reply_text(
        "⚙️ **Settings: Privacy Mode**\n\n"
        "Current LLM Provider: **OpenRouter (Default)**\n\n"
        "To use your own API Key (BYOK) for maximum privacy, please visit the dashboard:\n"
        "http://localhost:3000/settings",
        parse_mode="Markdown"
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    The main conversation loop. Forwards text to Backend Router.
    """
    chat_id = update.effective_chat.id
    text = update.message.text
    
    # 1. Auth Check (Double check for every message)
    if not await is_authenticated(chat_id):
        # Silent ignore or remind? 
        # Better to remind gently.
        await start(update, context)
        return

    # 2. Forward to Backend
    # We will hit the /chat endpoint of the running FastAPI app
    # Assumption: POST /chat { "message": text, "session_id": str(chat_id) }
    
    await update.message.reply_chat_action(action="typing")
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{BACKEND_API_URL}/chat",  # Adjust endpoint as needed based on backend/app/main.py
                json={
                    "message": text,
                    "thread_id": str(chat_id) # Using chat_id as thread_id for memory
                }
            )
            
        if response.status_code == 200:
            data = response.json()
            # Expecting data to contain "response" or similar
            # The backend returns 'messages' list, we need to extract the last AIMessage content
            messages = data.get("messages", [])
            bot_reply = "..."
            if messages:
                last_msg = messages[-1]
                if isinstance(last_msg, dict):
                    bot_reply = last_msg.get("content", "...")
                elif hasattr(last_msg, "content"):
                    bot_reply = last_msg.content
            
            await update.message.reply_text(bot_reply)
        else:
            logging.error(f"Backend Error: {response.status_code} - {response.text}")
            await update.message.reply_text("⚠️ **System Error**: The backend neural link is unresponsive.")
            
    except Exception as e:
        logging.error(f"Network Error: {e}")
        await update.message.reply_text("⚠️ **Connection Error**: backend unreachable.")

