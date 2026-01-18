import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from telegram import Update, User, Chat, Message
from telegram.ext import ContextTypes
from services.kairos_bot.handlers import start, handle_message

# Mock Update and Context
@pytest.fixture
def mock_update():
    update = MagicMock(spec=Update)
    update.effective_user = MagicMock(spec=User)
    update.effective_user.first_name = "TestUser"
    update.effective_chat = MagicMock(spec=Chat)
    update.effective_chat.id = 12345
    update.message = AsyncMock(spec=Message)
    update.message.text = "Hello Bot"
    update.message.reply_text = AsyncMock()
    update.message.reply_chat_action = AsyncMock()
    return update

@pytest.fixture
def mock_context():
    context = MagicMock(spec=ContextTypes.DEFAULT_TYPE)
    return context

@pytest.mark.asyncio
async def test_start_unauthenticated(mock_update, mock_context):
    """
    Test /start when user is NOT authenticated.
    Should reply with an auth link.
    """
    with patch("services.kairos_bot.handlers.is_authenticated", return_value=False):
         with patch("services.kairos_bot.handlers.generate_login_link", return_value="http://login"):
            await start(mock_update, mock_context)
            
            # Verify reply_text was called
            mock_update.message.reply_text.assert_called_once()
            args, kwargs = mock_update.message.reply_text.call_args
            assert "Authentication Required" in args[0]
            assert "reply_markup" in kwargs

@pytest.mark.asyncio
async def test_start_authenticated(mock_update, mock_context):
    """
    Test /start when user IS authenticated.
    Should reply with a welcome message.
    """
    with patch("services.kairos_bot.handlers.is_authenticated", return_value=True):
        await start(mock_update, mock_context)
        
        mock_update.message.reply_text.assert_called_once()
        args, _ = mock_update.message.reply_text.call_args
        assert "Systems Online" in args[0]

@pytest.mark.asyncio
async def test_handle_message_authenticated_success(mock_update, mock_context):
    """
    Test message handling when authenticated and backend responds 200.
    """
    with patch("services.kairos_bot.handlers.is_authenticated", return_value=True):
        # Mock httpx.AsyncClient response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"response": "Processed Message"}
        
        with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
             mock_post.return_value = mock_response
             
             await handle_message(mock_update, mock_context)
             
             # Verify backend was called
             mock_post.assert_called_once()
             # Verify bot replied with backend response
             mock_update.message.reply_text.assert_called_with("Processed Message")

@pytest.mark.asyncio
async def test_handle_message_unauthenticated(mock_update, mock_context):
    """
    Test message handling when NOT authenticated.
    Should redirect to start (which prompts login).
    """
    with patch("services.kairos_bot.handlers.is_authenticated", return_value=False):
        # We need to mock start as well to verify it's called, 
        # or just rely on the side effect of start being called (which we tested above).
        # Here we'll patch start to ensure it is awaited.
        with patch("services.kairos_bot.handlers.start", new_callable=AsyncMock) as mock_start:
            await handle_message(mock_update, mock_context)
            mock_start.assert_awaited_once_with(mock_update, mock_context)
