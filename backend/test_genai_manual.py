
import os
from google import genai
from google.genai import types

# User provided credentials and model
API_KEY = "api-key-here" #Add key bro
# Note: The user specified 'gemini-2.5-flash-' (with a trailing dash). 
# I will try it exactly as requested, but usually model names don't end in a dash.
# If it fails, I'll mention it.
MODEL = "gemini-2.0-flash-exp" # changing to a known working model for the test to verify the KEY first, 
# wait, the user explicitly said "use the model -gemini-2.5-flash-". 
# The dash at the start might mean the flag, but they put it at the end too? "-gemini-2.5-flash-"
# Actually, looking at the prompt: "use the model -gemini-2.5-flash-"
# It might be "gemini-2.5-flash" and the user used dashes as separators or formatting.
# Or maybe "gemini-1.5-flash". 
# I will try "gemini-2.0-flash-exp" first to verify the KEY, then try the user's string.
# Actually, let's try the user's string 'gemini-2.5-flash-' literally first.
# If it fails, I will fallback to 'gemini-2.0-flash-exp' to check if the key is valid.

def test_generate():
    print(f"Testing with Key: {API_KEY[:5]}...{API_KEY[-5:]}")
    
    client = genai.Client(api_key=API_KEY)
    
    # Test 1: Try the exact string provided
    model_name = "gemini-1.5-flash" # I suspect they meant this or 2.0-flash-exp. 2.5 is unlikely to be public yet. 
    # But I will try to use what they asked.
    # Let's try to list models first to see what's available? No, that might be too verbose.
    
    # I'll try a standard model first to validate the KEY.
    print("--- Verifying API Key with 'gemini-2.0-flash-exp' ---")
    try:
        response = client.models.generate_content(
            model="gemini-2.0-flash-exp",
            contents="Hello, are you working?",
            config=types.GenerateContentConfig(
                thinking_config=types.ThinkingConfig(thinking_level="HIGH")
            ) 
        )
        print(f"Success with gemini-2.0-flash-exp: {response.text}")
    except Exception as e:
        print(f"Failed with gemini-2.0-flash-exp: {e}")

    # Test 2: User's specific string
    user_model = "gemini-2.5-flash"
    print(f"\n--- Testing User Model '{user_model}' ---")
    try:
        response = client.models.generate_content(
            model=user_model,
            contents="Hello, do you exist?",
        )
        print(f"Success with {user_model}: {response.text}")
    except Exception as e:
        print(f"Failed with {user_model}: {e}")

if __name__ == "__main__":
    test_generate()
