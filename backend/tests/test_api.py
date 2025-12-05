"""Quick test with real Google AI API"""
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Load .env BEFORE importing llm_client
from dotenv import load_dotenv
env_path = os.path.join(os.path.dirname(__file__), '..', '.env')
load_dotenv(dotenv_path=env_path)

# NOW import llm_client (after env is loaded)
from apps import llm_client

# Verify API key is loaded
api_key = os.getenv('GOOGLE_AI_API_KEY')
if api_key:
    print(f"✅ API Key loaded: {api_key[:20]}...{api_key[-4:]}\n")
else:
    print("❌ API Key NOT loaded! Check .env file location\n")

# Test 1: Health Check
print("=== Health Check ===")
result = llm_client.health_check()
print(f"Status: {'✅' if result['ok'] else '❌'}")
print(f"Latency: {result['meta'].get('latency_ms', 'N/A')}ms\n")

# Test 2: Generate Fix
print("=== Generate Fix ===")
code = """def MyFunction():
    x = 5
    return x"""

result = llm_client.generate_fix(
    file_path="test.py",
    file_content=code,
    issue={"rule": "C0103", "message": "Function name should be lowercase", "line": 1}
)

print(f"Success: {result['success']}")
if result['success']:
    print(f"Patched:\n{result['patched_code']}")
    print(f"Explanation: {result['explanation']}")
    print(f"Tokens used: {result['meta'].get('tokens_used', 'N/A')}")
else:
    print(f"Error: {result['meta'].get('error')}")