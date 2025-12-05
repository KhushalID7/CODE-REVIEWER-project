"""Check available models for your API key"""
import os
import requests
from dotenv import load_dotenv

# Load environment variables
env_path = os.path.join(os.path.dirname(__file__), '..', '.env')
load_dotenv(dotenv_path=env_path)

api_key = os.getenv('GOOGLE_AI_API_KEY')

if not api_key:
    print("❌ No API key found!")
    exit(1)

print(f"✅ Using API key: {api_key[:20]}...{api_key[-4:]}\n")

# List available models
url = f"https://generativelanguage.googleapis.com/v1beta/models?key={api_key}"

print("Fetching available models...\n")
response = requests.get(url)

if response.status_code == 200:
    data = response.json()
    models = data.get('models', [])
    
    print(f"Found {len(models)} models:\n")
    print("=" * 80)
    
    for model in models:
        name = model.get('name', 'N/A')
        display_name = model.get('displayName', 'N/A')
        supported_methods = model.get('supportedGenerationMethods', [])
        
        # Check if it supports generateContent
        supports_generate = 'generateContent' in supported_methods
        
        if supports_generate:
            print(f"✅ {name}")
            print(f"   Display Name: {display_name}")
            print(f"   Methods: {', '.join(supported_methods)}")
            print()
    
    print("=" * 80)
    print("\n💡 Use one of the model names above in your .env file")
    print("   Example: GOOGLE_AI_MODEL=models/gemini-1.5-flash")
    
else:
    print(f"❌ Error {response.status_code}: {response.text}")