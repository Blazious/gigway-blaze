import os
import django
import json

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'escrow_platform.settings')
django.setup()

from core.intasend_gateway import get_intasend_service
from core.models import Escrow

e = Escrow.objects.get(id="e00a188a-7f8e-4eb9-b70e-7420bd48e472")
service = get_intasend_service()
try:
    response = service.transfer.status(e.mpesa_conversation_id)
    print("STATUS:", json.dumps(response, indent=2))
except Exception as err:
    print("ERROR:", str(err))
