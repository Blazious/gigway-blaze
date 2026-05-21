import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'escrow_platform.settings')
django.setup()

from core.intasend_gateway import initiate_escrow_deposit

try:
    print(initiate_escrow_deposit('254712345678', 50, 'test1234'))
except Exception as e:
    import traceback
    traceback.print_exc()
