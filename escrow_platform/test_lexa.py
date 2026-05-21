import os
from dotenv import load_dotenv
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'escrow_platform.settings')
django.setup()

from core.ai_dispute_analyzer import get_lexa_response

# Test Lexa
print("Testing Lexa...")
response = get_lexa_response("Hi Lexa, tell me about the escrow process.")
print(f"Lexa Response: {response}")
