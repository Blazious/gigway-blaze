#!/usr/bin/env python
"""
Simple Deposit Test - Non-interactive version
Usage: python test_deposit_simple.py <client_phone> <freelancer_phone> [amount]
Example: python test_deposit_simple.py 254712345678 254798765432 10
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
from core.models import Project, Contract, Escrow
from core.mpesa_stk import initiate_stk_push, format_phone_number
from core.mpesa_callbacks import process_deposit_callback
from core.contract_generator import generate_contract_text
from django.utils import timezone
from datetime import timedelta

User = get_user_model()

def test_deposit(client_phone_raw, freelancer_phone_raw, amount=10.00):
    """Test deposit flow with provided phone numbers"""
    print("\n" + "="*60)
    print("DEPOSIT TEST")
    print("="*60 + "\n")
    
    # Format phone numbers
    client_phone = format_phone_number(client_phone_raw)
    freelancer_phone = format_phone_number(freelancer_phone_raw)
    
    client_email = f"test_client_{datetime.now().strftime('%Y%m%d%H%M%S')}@test.com"
    freelancer_email = f"test_freelancer_{datetime.now().strftime('%Y%m%d%H%M%S')}@test.com"
    
    print(f"Client: {client_email} ({client_phone})")
    print(f"Freelancer: {freelancer_email} ({freelancer_phone})")
    print(f"Amount: KES {amount}\n")
    
    try:
        # Create client
        client = User.objects.create_user(
            email=client_email,
            password="testpass123",
            phone_number=client_phone,
            user_type='client'
        )
        print(f"✓ Client created: {client.email}")
        
        # Create freelancer
        freelancer = User.objects.create_user(
            email=freelancer_email,
            password="testpass123",
            phone_number=freelancer_phone,
            user_type='freelancer'
        )
        print(f"✓ Freelancer created: {freelancer.email}")
        
        # Create project
        project = Project.objects.create(
            client=client,
            freelancer=freelancer,
            title="Test Deposit Project",
            description='Testing deposit flow',
            scope_of_work='Test',
            timeline=timezone.now().date() + timedelta(days=7),
            budget=amount,
            status='assigned'
        )
        print(f"✓ Project created: {project.id}")
        
        # Create and sign contract
        contract = Contract.objects.create(
            project=project,
            freelancer=freelancer,
            client=client,
            contract_text=generate_contract_text(project),
            amount=amount,
            client_signature=f"test_client_{datetime.now().timestamp()}",
            freelancer_signature=f"test_freelancer_{datetime.now().timestamp()}",
            client_signed_at=timezone.now(),
            freelancer_signed_at=timezone.now(),
            status='signed'
        )
        print(f"✓ Contract signed")
        
        # Create escrow
        escrow = Escrow.objects.create(
            contract=contract,
            amount=amount,
            status='pending'
        )
        print(f"✓ Escrow created: {escrow.id}")
        
        # Initiate STK Push
        print(f"\n{'='*60}")
        print("INITIATING M-PESA STK PUSH...")
        print(f"{'='*60}\n")
        
        checkout_id = initiate_stk_push(
            phone_number=client_phone,
            amount=float(amount),
            account_reference=f"ESCROW-{project.id}",
            transaction_desc=f"Payment for {project.title}"
        )
        
        print(f"✓ STK Push initiated!")
        print(f"  Checkout Request ID: {checkout_id}\n")
        
        escrow.mpesa_checkout_request_id = checkout_id
        escrow.save()
        
        print(f"{'='*60}")
        print("ACTION REQUIRED:")
        print("1. Check your phone for M-Pesa prompt")
        print("2. Enter your M-Pesa PIN")
        print("3. Complete the payment")
        print(f"{'='*60}\n")
        
        print("After payment, run this script again with --simulate-callback flag")
        print("OR manually check the escrow status in Django admin\n")
        
        print(f"Project ID: {project.id}")
        print(f"Escrow ID: {escrow.id}")
        print(f"Checkout ID: {checkout_id}")
        
        return {
            'success': True,
            'project_id': str(project.id),
            'escrow_id': str(escrow.id),
            'checkout_id': checkout_id
        }
        
    except Exception as e:
        print(f"\n✗ ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        return {'success': False, 'error': str(e)}

def simulate_callback(checkout_id):
    """Simulate a successful callback"""
    print("\n" + "="*60)
    print("SIMULATING CALLBACK")
    print("="*60 + "\n")
    
    try:
        escrow = Escrow.objects.get(mpesa_checkout_request_id=checkout_id)
        project = escrow.contract.project
        
        callback_data = json.dumps({
            "Body": {
                "stkCallback": {
                    "CheckoutRequestID": checkout_id,
                    "ResultCode": 0,
                    "ResultDesc": "The service request is processed successfully.",
                    "CallbackMetadata": {
                        "Item": [
                            {"Name": "Amount", "Value": str(int(escrow.amount))},
                            {"Name": "MpesaReceiptNumber", "Value": f"TEST{datetime.now().strftime('%Y%m%d%H%M%S')}"},
                            {"Name": "TransactionDate", "Value": datetime.now().strftime('%Y%m%d%H%M%S')},
                            {"Name": "PhoneNumber", "Value": escrow.client_phone}
                        ]
                    }
                }
            }
        })
        
        success, message = process_deposit_callback(callback_data.encode('utf-8'))
        
        if success:
            escrow.refresh_from_db()
            project.refresh_from_db()
            
            print(f"✓ Callback processed: {message}")
            print(f"\nEscrow Status: {escrow.status}")
            print(f"Receipt: {escrow.mpesa_receipt}")
            print(f"Project Status: {project.status}")
            print(f"Deposited At: {escrow.deposited_at}")
            
            return True
        else:
            print(f"✗ Callback failed: {message}")
            return False
            
    except Escrow.DoesNotExist:
        print(f"✗ Escrow not found for checkout ID: {checkout_id}")
        return False
    except Exception as e:
        print(f"✗ ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    if len(sys.argv) < 3:
        print("Usage:")
        print("  Test deposit: python test_deposit_simple.py <client_phone> <freelancer_phone> [amount]")
        print("  Simulate callback: python test_deposit_simple.py --simulate-callback <checkout_id>")
        print("\nExample:")
        print("  python test_deposit_simple.py 254712345678 254798765432 10")
        print("  python test_deposit_simple.py --simulate-callback abc123xyz")
        sys.exit(1)
    
    if sys.argv[1] == '--simulate-callback':
        if len(sys.argv) < 3:
            print("Error: Checkout ID required")
            sys.exit(1)
        simulate_callback(sys.argv[2])
    else:
        client_phone = sys.argv[1]
        freelancer_phone = sys.argv[2]
        amount = float(sys.argv[3]) if len(sys.argv) > 3 else 10.00
        
        result = test_deposit(client_phone, freelancer_phone, amount)
        
        if result.get('success'):
            print(f"\n✓ Test initiated successfully!")
            print(f"Checkout ID: {result['checkout_id']}")
            print(f"\nTo simulate callback, run:")
            print(f"python test_deposit_simple.py --simulate-callback {result['checkout_id']}")
