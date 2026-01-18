import httpx
from .config import BACKEND_API_URL

async def is_authenticated(telegram_id: int) -> bool:
    """
    Checks if the user is authenticated by querying the backend.
    """
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            # Pass user_id to verify specific user
            response = await client.get(f"{BACKEND_API_URL}/auth/status", params={"user_id": str(telegram_id)})
            if response.status_code == 200:
                data = response.json()
                return data.get("authenticated", False)
    except Exception as e:
        print(f"Auth check failed: {e}")
        return False
    return False

def generate_login_link(telegram_id: int, backend_url: str) -> str:
    """
    Generates the OAuth login link.
    """
    # First, get the dynamic auth URL from backend
    # But since we can't await here easily if this is synchronous...
    # Actually, we can just construct the link to the backend redirector
    # which will then redirect to Google.
    base_url = backend_url.rstrip("/")
    return f"{base_url}/auth/login?user_id={telegram_id}"
