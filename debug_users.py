import os
import django
import sys

# Add project root to path if needed (e.g. for imports to work)
sys.path.append(os.getcwd())

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'escrow_platform.settings')
django.setup()

from core.models import CustomUser

print(f"Total Users: {CustomUser.objects.count()}")
for u in CustomUser.objects.all():
    print("-" * 30)
    print(f"Email:  {u.email}")
    print(f"Active: {u.is_active}")
    print(f"Usable Pass: {u.has_usable_password()}")
    print("-" * 30)
