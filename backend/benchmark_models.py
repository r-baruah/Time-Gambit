
import os
import time
from openrouter import OpenRouter
from dotenv import load_dotenv

# Load environment variables
load_dotenv(".env")

api_key = os.getenv("OPENROUTER_API_KEY")
if not api_key:
    print("Error: OPENROUTER_API_KEY not found in .env")
    exit(1)

client = OpenRouter(api_key=api_key)

models_to_test = [
    "moonshotai/kimi-k2",
    "z-ai/glm-4.5-air:free"
]

print(f"{'Model':<30} | {'Status':<10} | {'Time (s)':<10} | {'Response Preview'}")
print("-" * 100)

for model in models_to_test:
    start_time = time.time()
    try:
        response = client.chat.send(
            model=model,
            messages=[
                {"role": "user", "content": "Hello, simply say 'OK' if you can hear me."}
            ],
            temperature=0
        )
        end_time = time.time()
        duration = end_time - start_time
        content = response.choices[0].message.content.strip()
        status = "WORKING"
    except Exception as e:
        end_time = time.time()
        duration = end_time - start_time
        content = f"Error: {str(e)[:40]}..."
        status = "FAILED"

    print(f"{model:<30} | {status:<10} | {duration:<10.4f} | {content[:40].replace('\n', ' ')}")
