from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters
from .config import TELEGRAM_BOT_TOKEN
from .handlers import start, help_command, settings, handle_message
import logging
import logging
import asyncio

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

def main():
    if not TELEGRAM_BOT_TOKEN:
        print("Error: TELEGRAM_BOT_TOKEN not found in environment variables.")
        return

    application = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()
    
    # Register Handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("settings", settings))
    
    # Message Handler (Text & Not Command)
    application.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))
    
    print("Kairos Bot is starting...")
    application.run_polling()

if __name__ == '__main__':
    main()
