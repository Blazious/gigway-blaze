from core.models import Project, Contract, Proposal
from core.contract_generator import generate_contract_text

# Get the project
project_id = '75c42f95-600d-4478-b330-7fdad9ee0312'
project = Project.objects.get(id=project_id)

print(f"Project: {project.title}")
print(f"Status: {project.status}")
print(f"Freelancer: {project.freelancer}")

# Check if contract exists
contracts = Contract.objects.filter(project=project)
print(f"\nContracts found: {contracts.count()}")

if contracts.exists():
    contract = contracts.first()
    print(f"Contract ID: {contract.id}")
    print(f"Contract Status: {contract.status}")
else:
    print("\nNo contract found! Creating one now...")
    contract = Contract.objects.create(
        project=project,
        contract_text=generate_contract_text(project),
        status='pending'
    )
    print(f"✅ Contract created! ID: {contract.id}")
    print(f"Contract Status: {contract.status}")
