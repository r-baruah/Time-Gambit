import os
from dotenv import load_dotenv

# Load environment variables from the root .env file
# Assuming .env is in the backend implementation root
load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
BACKEND_API_URL = os.getenv("BACKEND_API_URL", "http://localhost:8000")
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
