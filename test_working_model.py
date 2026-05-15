import os
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv('GEMINI_API_KEY')
genai.configure(api_key=api_key)

print("Listing all models and testing the first available for generateContent...")
models = list(genai.list_models())
generate_models = [m for m in models if 'generateContent' in m.supported_generation_methods]

if not generate_models:
    print("No models found that support generateContent.")
else:
    for m in generate_models:
        print(f"Testing model: {m.name}")
        try:
            model = genai.GenerativeModel(m.name)
            response = model.generate_content("Hello")
            print(f"SUCCESS with {m.name}: {response.text[:50]}...")
            break # Stop at first success
        except Exception as e:
            print(f"FAILED with {m.name}: {e}")
