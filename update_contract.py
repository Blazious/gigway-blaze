import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'escrow_platform.settings')
django.setup()

from core.models import Project, Contract
from core.contract_generator import generate_contract_text

# Get test project
project = Project.objects.get(id='162bb8be-699c-40a1-b3b3-ffb37be2a9e3')
contract = Contract.objects.get(project=project)

# Regenerate contract
contract.contract_text = generate_contract_text(project)
contract.save()

print(f"✅ Contract updated successfully!")
print(f"Contract ID: {contract.id}")
print(f"Project: {project.title}")
print(f"Status: {contract.status}")
