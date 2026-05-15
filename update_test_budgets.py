import os
import django
from decimal import Decimal
import re

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'escrow_platform.settings')
django.setup()

from core.models import Project, Escrow, Contract

def update_budgets():
    new_budget = Decimal('3.00')
    
    # Update all projects (excluding the very first one maybe? No, user said "the amounts")
    # I'll update all projects created by the client blaziousmwambuwa@gmail.com
    projects = Project.objects.filter(client__email='blaziousmwambuwa@gmail.com')
    
    for p in projects:
        old_budget = p.budget
        p.budget = new_budget
        p.save()
        
        # Update related Escrow
        contract = Contract.objects.filter(project=p).first()
        escrow = Escrow.objects.filter(contract=contract).first() if contract else None
        if escrow:
            escrow.amount = new_budget
            escrow.save()
            
        # Update Contract text if exists
        if contract:
            # Replace budget in text using regex to be safe
            # Budget usually looks like "KES 15,000.00" or similar
            text = contract.contract_text
            # Simple replacement for "KES [numbers]"
            new_text = re.sub(r'KES [\d,.]+', f'KES {new_budget:,.2f}', text)
            contract.contract_text = new_text
            contract.save()
            
        print(f"Updated '{p.title}': {old_budget} -> {new_budget}")

if __name__ == "__main__":
    update_budgets()
