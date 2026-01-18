from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage, BaseMessage
from app.config import settings
import os

class GoogleGenAIWrapper:
    """
    Custom wrapper for Google GenAI SDK to be compatible with LangChain interface.
    Supports 'Thinking' and 'Google Search' tools.
    """
    def __init__(self, api_key: str, model: str = "gemini-2.0-flash-thinking-exp-01-21", **kwargs):
        try:
            from google import genai
            from google.genai import types
            self.client = genai.Client(api_key=api_key)
            self.model = model
            self.types = types
            self.kwargs = kwargs
            self._is_functional = True
        except ImportError:
            print("Error: google-genai not installed.")
            self._is_functional = False

    def invoke(self, messages: list[BaseMessage]) -> AIMessage:
        if not self._is_functional:
            return AIMessage(content="Error: google-genai library is missing. Please install it.")

        # Convert LangChain messages to Google Content
        contents = []
        
        for msg in messages:
            if isinstance(msg, SystemMessage):
                contents.append(self.types.Content(
                    role="user", 
                    parts=[self.types.Part.from_text(text=f"System Instruction: {msg.content}")]
                ))
            elif isinstance(msg, HumanMessage):
                contents.append(self.types.Content(
                    role="user",
                    parts=[self.types.Part.from_text(text=msg.content)]
                ))
            elif isinstance(msg, AIMessage):
                contents.append(self.types.Content(
                    role="model",
                    parts=[self.types.Part.from_text(text=msg.content)]
                ))

        # Config - only add thinking for thinking models
        is_thinking_model = "thinking" in self.model.lower()
        
        config_kwargs = {}
        
        if is_thinking_model:
            config_kwargs["thinking_config"] = self.types.ThinkingConfig(thinking_level="HIGH")
            # Thinking models also support search
            config_kwargs["tools"] = [self.types.Tool(googleSearch=self.types.GoogleSearch())]
        
        generate_content_config = self.types.GenerateContentConfig(**config_kwargs) if config_kwargs else None

        try:
            response = self.client.models.generate_content(
                model=self.model,
                contents=contents,
                config=generate_content_config
            )
            # Handle response safely
            if response.text:
                return AIMessage(content=response.text)
            else:
                # Fallback if text is empty (sometimes happens with search results or thinking only)
                # But usually there is text.
                return AIMessage(content="[No response text generated]")
                
        except Exception as e:
            print(f"Google GenAI Error: {e}")
            return AIMessage(content=f"Error calling Google API: {str(e)}")

def get_llm():
    """
    Factory to get the configured LLM based on Settings.
    """
    provider = settings.LLM_PROVIDER.lower()
    
    if provider == "openai":
        if not settings.OPENAI_API_KEY:
             print("Warning: OPENAI_API_KEY is missing.")
        return ChatOpenAI(
            api_key=settings.OPENAI_API_KEY,
            model=settings.OPENAI_MODEL,
            temperature=0
        )
        
    elif provider == "google":
        if not settings.GOOGLE_API_KEY:
            print("Warning: GOOGLE_API_KEY is missing.")
        # Use custom wrapper
        return GoogleGenAIWrapper(
            api_key=settings.GOOGLE_API_KEY,
            model=settings.GOOGLE_MODEL or "gemini-2.5-flash"
        )
            
    # Default: OpenRouter
    return ChatOpenAI(
        api_key=settings.OPENROUTER_API_KEY,
        base_url="https://openrouter.ai/api/v1",
        model=settings.OPENROUTER_MODEL,
        temperature=0
    )
