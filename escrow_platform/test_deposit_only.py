#!/usr/bin/env python
"""
Quick Deposit Test - Tests just the deposit flow
"""
import os
import sys
import django
import json
from datetime import datetime

# Setup Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'escrow_platform.settings')
django.setup()

from django.contrib.auth import get_user_model
from core.models import Project, Proposal, Contract, Escrow
from core.mpesa_stk import initiate_stk_push, format_phone_number
from core.mpesa_callbacks import process_deposit_callback
from core.contract_generator import generate_contract_text
from django.utils import timezone
from datetime import timedelta

User = get_user_model()

def test_deposit():
    """Quick test of deposit flow"""
    print("\n" + "="*60)
    print("QUICK DEPOSIT TEST")
    print("="*60 + "\n")
    
    # Get or create test users
    client_email = input("Enter client email (or press Enter for test@client.com): ").strip() or "test@client.com"
    freelancer_email = input("Enter freelancer email (or press Enter for test@freelancer.com): ").strip() or "test@freelancer.com"
    
    client_phone = input("Enter CLIENT phone (e.g., 254712345678): ").strip()
    freelancer_phone = input("Enter FREELANCER phone (e.g., 254798765432): ").strip()
    
    client_phone = format_phone_number(client_phone)
    freelancer_phone = format_phone_number(freelancer_phone)
    
    print(f"\nClient: {client_email} ({client_phone})")
    print(f"Freelancer: {freelancer_email} ({freelancer_phone})")
    
    try:
        # Get or create client
        client, _ = User.objects.get_or_create(
            email=client_email,
            defaults={
                'phone_number': client_phone,
                'user_type': 'client',
                'password': 'pbkdf2_sha256$test'  # Dummy password
            }
        )
        if client.phone_number != client_phone:
            client.phone_number = client_phone
            client.save()
        
        # Get or create freelancer
        freelancer, _ = User.objects.get_or_create(
            email=freelancer_email,
            defaults={
                'phone_number': freelancer_phone,
                'user_type': 'freelancer',
                'password': 'pbkdf2_sha256$test'  # Dummy password
            }
        )
        if freelancer.phone_number != freelancer_phone:
            freelancer.phone_number = freelancer_phone
            freelancer.save()
        
        # Create or get project
        project, created = Project.objects.get_or_create(
            client=client,
            title="Quick Test Project",
            defaults={
                'description': 'Quick deposit test',
                'scope_of_work': 'Test',
                'timeline': timezone.now().date() + timedelta(days=7),
                'budget': 10.00,
                'status': 'open'
            }
        )
        
        if not created:
            print(f"Using existing project: {project.id}")
        
        # Assign freelancer if not assigned
        if not project.freelancer:
            project.freelancer = freelancer
            project.status = 'assigned'
            project.save()
        
        # Create contract if not exists
        contract, created = Contract.objects.get_or_create(
            project=project,
            defaults={
                'contract_text': generate_contract_text(project),
                'amount': project.budget,
                'client': project.client,
                'freelancer': project.freelancer,
                'status': 'pending_signature'
            }
        )
        
        # Sign contract (both parties)
        if not contract.client_signature:
            contract.client_signature = f"test_signature_{datetime.now().timestamp()}"
            contract.client_signed_at = timezone.now()
        
        if not contract.freelancer_signature:
            contract.freelancer_signature = f"test_signature_{datetime.now().timestamp()}"
            contract.freelancer_signed_at = timezone.now()
        
        if contract.client_signature and contract.freelancer_signature:
            contract.status = 'signed'
        contract.save()
        
        print(f"\n✓ Contract signed: {contract.status}")
        
        # Create or get escrow
        escrow, created = Escrow.objects.get_or_create(
            contract=contract,
            defaults={
                'amount': project.budget,
                'status': 'pending'
            }
        )
        
        if not created:
            escrow.amount = project.budget
            escrow.save()
        
        print(f"\n✓ Escrow created: {escrow.id}")
        print(f"  Status: {escrow.status}")
        print(f"  Amount: {escrow.amount}")
        print(f"  Client Phone: {project.client.phone_number}")
        print(f"  Freelancer Phone: {project.freelancer.phone_number}")
        
        # Initiate STK Push
        print(f"\n{'='*60}")
        print("INITIATING M-PESA STK PUSH...")
        print(f"{'='*60}\n")
        
        try:
            checkout_id = initiate_stk_push(
                phone_number=client_phone,
                amount=float(project.budget),
                account_reference=f"ESCROW-{project.id}",
                transaction_desc=f"Payment for {project.title}"
            )
            
            print(f"✓ STK Push initiated!")
            print(f"  Checkout Request ID: {checkout_id}")
            
            escrow.mpesa_checkout_request_id = checkout_id
            escrow.status = 'pending'
            escrow.save()
            
            print(f"\n{'='*60}")
            print("ACTION REQUIRED:")
            print("1. Check your phone for M-Pesa prompt")
            print("2. Enter your M-Pesa PIN")
            print("3. Complete the payment")
            print(f"{'='*60}\n")
            
            input("Press ENTER after completing payment on your phone...")
            
            # Simulate callback
            print("\nSimulating callback...")
            success = input("Did payment succeed? (y/n): ").strip().lower()
            
            if success == 'y':
                callback_data = json.dumps({
                    "Body": {
                        "stkCallback": {
                            "CheckoutRequestID": checkout_id,
                            "ResultCode": 0,
                            "ResultDesc": "The service request is processed successfully.",
                            "CallbackMetadata": {
                                "Item": [
                                    {"Name": "Amount", "Value": str(int(project.budget))},
                                    {"Name": "MpesaReceiptNumber", "Value": f"TEST{datetime.now().strftime('%Y%m%d%H%M%S')}"},
                                    {"Name": "TransactionDate", "Value": datetime.now().strftime('%Y%m%d%H%M%S')},
                                    {"Name": "PhoneNumber", "Value": client_phone}
                                ]
                            }
                        }
                    }
                })
                
                success, message = process_deposit_callback(callback_data.encode('utf-8'))
                
                if success:
                    escrow.refresh_from_db()
                    project.refresh_from_db()
                    
                    print(f"\n{'='*60}")
                    print("✓ DEPOSIT SUCCESSFUL!")
                    print(f"{'='*60}")
                    print(f"Escrow Status: {escrow.status}")
                    print(f"Receipt: {escrow.mpesa_receipt}")
                    print(f"Project Status: {project.status}")
                    print(f"{'='*60}\n")
                else:
                    print(f"✗ Callback failed: {message}")
            else:
                print("Payment not completed - skipping callback")
            
        except Exception as e:
            print(f"\n✗ ERROR: {str(e)}")
            import traceback
            traceback.print_exc()
            return False
        
        return True
        
    except Exception as e:
        print(f"\n✗ ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    test_deposit()
