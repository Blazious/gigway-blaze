import os
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv('GEMINI_API_KEY')
print(f"DEBUG: Key starts with: {api_key[:10]}...")

genai.configure(api_key=api_key)

print("--- ALL MODELS ---")
try:
    for m in genai.list_models():
        print(f"Name: {m.name}")
        print(f"Methods: {m.supported_generation_methods}")
        print("-" * 20)
except Exception as e:
    print(f"CRITICAL ERROR: {e}")
