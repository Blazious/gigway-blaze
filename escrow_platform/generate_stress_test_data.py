import os
import django
import uuid
from decimal import Decimal

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'escrow_platform.settings')
django.setup()

from core.models import CustomUser, Project, Contract, Escrow, Proposal

def generate_test_data():
    client = CustomUser.objects.filter(email='blaziousmwambuwa@gmail.com').first()
    freelancer = CustomUser.objects.filter(email='netflixmabirikani@gmail.com').first()

    if not client or not freelancer:
        print("Error: Client or Freelancer user not found.")
        return

    projects_data = [
        {
            "title": "Mobile App UI/UX Design",
            "description": "Design a 10-screen mobile app for a fitness tracking startup.",
            "budget": 15000,
            "status": "in_progress",
            "escrow_status": "held"
        },
        {
            "title": "Data Scraping for Real Estate",
            "description": "Scrape 5000 listings from various real estate websites.",
            "budget": 8000,
            "status": "in_progress",
            "escrow_status": "held"
        },
        {
            "title": "Python Backend Bug Fixes",
            "description": "Fix 5 critical bugs in our Django backend.",
            "budget": 5000,
            "status": "assigned",
            "escrow_status": "pending"
        },
        {
            "title": "Logo Design - Tech Company",
            "description": "Create a modern logo for a new AI startup.",
            "budget": 3500,
            "status": "open",
            "escrow_status": None
        },
        {
            "title": "Blog Writing - Cybersecurity",
            "description": "Write 4 long-form articles about cybersecurity trends.",
            "budget": 6000,
            "status": "in_progress",
            "escrow_status": "held"
        }
    ]

    for data in projects_data:
        from datetime import date, timedelta
        p = Project.objects.create(
            client=client,
            title=data['title'],
            description=data['description'],
            scope_of_work=data['description'], # Using description as scope for simplicity
            timeline=date.today() + timedelta(days=30),
            budget=Decimal(data['budget']),
            status=data['status'] if data['status'] != 'open' else 'open'
        )
        
        if data['status'] != 'open':
            p.freelancer = freelancer
            p.save()
            
            # Create a signed contract
            from core.contract_generator import generate_contract_text
            contract = Contract.objects.create(
                project=p,
                client=client,
                freelancer=freelancer,
                contract_text=generate_contract_text(p),
                amount=p.budget,
                client_signature="Signed by Client",
                freelancer_signature="Signed by Freelancer",
                status='signed'
            )
            
            # Create Escrow if needed
            if data['escrow_status']:
                Escrow.objects.create(
                    contract=contract,
                    amount=p.budget,
                    status=data['escrow_status']
                )
        
        print(f"Created project: {p.title} - Status: {p.status}")

if __name__ == "__main__":
    generate_test_data()
