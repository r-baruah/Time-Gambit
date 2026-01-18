import httpx
import time

print("Testing AI Agent Backend...")
print("-" * 50)

start = time.time()
try:
    response = httpx.post(
        "http://localhost:8000/chat",
        json={"message": "hello"},
        timeout=60.0
    )
    end = time.time()
    print(f"Status: {response.status_code}")
    print(f"Time: {end - start:.2f}s")
    print(f"Response: {response.json()}")
except Exception as e:
    end = time.time()
    print(f"Error after {end - start:.2f}s: {e}")
