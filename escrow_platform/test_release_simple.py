#!/usr/bin/env python
"""
Simple Release Test - Test releasing escrow funds to freelancer
Usage: python test_release_simple.py [escrow_id]
       If no escrow_id provided, uses the most recent 'held' escrow
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
from core.models import Escrow, Deliverable, Project
from core.mpesa_b2c import send_b2c_payment
from core.mpesa_callbacks import process_b2c_callback
from django.utils import timezone

User = get_user_model()

def test_release(escrow_id=None):
    """Test releasing escrow funds to freelancer"""
    print("\n" + "="*60)
    print("RELEASE TEST - Withdraw Funds to Freelancer")
    print("="*60 + "\n")
    
    try:
        # Get escrow
        if escrow_id:
            escrow = Escrow.objects.get(id=escrow_id)
        else:
            # Get most recent 'held' escrow
            escrow = Escrow.objects.filter(status='held').order_by('-created_at').first()
        
        if not escrow:
            print("[X] No escrow found with status 'held'")
            print("\nAvailable escrows:")
            all_escrows = Escrow.objects.all().order_by('-created_at')[:5]
            for e in all_escrows:
                print(f"  ID: {e.id} | Status: {e.status} | Amount: {e.amount} | Project: {e.contract.project.title}")
            return False
        
        print(f"[OK] Found escrow: {escrow.id}")
        print(f"  Project: {escrow.contract.project.title}")
        print(f"  Amount: KES {escrow.amount}")
        print(f"  Status: {escrow.status}")
        print(f"  Client Phone: {escrow.contract.project.client.phone_number}")
        print(f"  Freelancer Phone: {escrow.contract.project.freelancer.phone_number}\n")
        
        if escrow.status != 'held':
            print(f"[X] Escrow status is '{escrow.status}' (expected 'held')")
            print("  Only escrows with 'held' status can be released")
            return False
        
        # Create deliverable
        print("Creating deliverable...")
        deliverable, created = Deliverable.objects.get_or_create(
            contract=escrow.contract,
            defaults={
                'file_paths': f"test_deliverable_{datetime.now().timestamp()}.pdf",
                'description': 'Test deliverable for release flow',
                'status': 'submitted'
            }
        )
        
        if created:
            print(f"[OK] Deliverable created: {deliverable.id}")
        else:
            print(f"[OK] Using existing deliverable: {deliverable.id}")
            deliverable.status = 'submitted'
            deliverable.save()
        
        # Approve deliverable and initiate B2C payment
        print(f"\n{'='*60}")
        print("INITIATING B2C PAYMENT TO FREELANCER...")
        print(f"{'='*60}\n")
        
        deliverable.status = 'approved'
        deliverable.save()
        
        # Send B2C payment
        payment_result = send_b2c_payment(
            phone_number=escrow.contract.project.freelancer.phone_number,
            amount=float(escrow.amount),
            occasion=f"Payment for {escrow.contract.project.title}",
            remarks="Freelancer payment via escrow"
        )
        
        print(f"[OK] B2C payment initiated!")
        print(f"  Conversation ID: {payment_result['conversation_id']}")
        print(f"  Amount: KES {escrow.amount}")
        print(f"  Recipient: {escrow.freelancer_phone}\n")
        
        # Update escrow
        escrow.mpesa_conversation_id = payment_result['conversation_id']
        escrow.status = 'releasing'
        escrow.save()
        
        # Update project status
        escrow.contract.project.status = 'completed'
        escrow.contract.project.save()
        
        print(f"{'='*60}")
        print("ACTION REQUIRED:")
        print("1. Check freelancer's phone for M-Pesa payment")
        print("2. Payment should arrive shortly")
        print(f"{'='*60}\n")
        
        print("After payment, run this script again with --simulate-callback flag")
        print(f"OR manually check the escrow status in Django admin\n")
        
        print(f"Escrow ID: {escrow.id}")
        print(f"Conversation ID: {payment_result['conversation_id']}")
        
        return {
            'success': True,
            'escrow_id': str(escrow.id),
            'conversation_id': payment_result['conversation_id']
        }
        
    except Escrow.DoesNotExist:
        print(f"[X] Escrow not found: {escrow_id}")
        return False
    except Exception as e:
        print(f"\n[X] ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def simulate_b2c_callback(conversation_id):
    """Simulate a successful B2C callback"""
    print("\n" + "="*60)
    print("SIMULATING B2C CALLBACK")
    print("="*60 + "\n")
    
    try:
        escrow = Escrow.objects.get(mpesa_conversation_id=conversation_id)
        
        print(f"Found escrow: {escrow.id}")
        print(f"Current status: {escrow.status}")
        print(f"Amount: KES {escrow.amount}\n")
        
        callback_data = json.dumps({
            "Result": {
                "ConversationID": conversation_id,
                "ResultCode": 0,
                "ResultDesc": "The service request is processed successfully.",
                "ResultParameters": {
                    "ResultParameter": [
                        {"Key": "TransactionReceipt", "Value": f"B2C{datetime.now().strftime('%Y%m%d%H%M%S')}"},
                        {"Key": "TransactionAmount", "Value": str(int(escrow.amount))},
                        {"Key": "B2CWorkingAccountAvailableFunds", "Value": "100000"},
                        {"Key": "B2CUtilityAccountAvailableFunds", "Value": "50000"},
                        {"Key": "TransactionCompletedDateTime", "Value": datetime.now().strftime('%Y.%m.%d %H:%M:%S')},
                        {"Key": "ReceiverPartyPublicName", "Value": f"{escrow.contract.project.freelancer.phone_number}"},
                        {"Key": "B2CChargesPaidAccountAvailableFunds", "Value": "0"},
                        {"Key": "B2CRecipientIsRegisteredCustomer", "Value": "Y"}
                    ]
                }
            }
        })
        
        success, message = process_b2c_callback(callback_data.encode('utf-8'))
        
        if success:
            escrow.refresh_from_db()
            escrow.project.refresh_from_db()
            
            print(f"[OK] Callback processed: {message}")
            print(f"\nEscrow Status: {escrow.status}")
            print(f"Release Receipt: {escrow.mpesa_release_receipt}")
            print(f"Released At: {escrow.released_at}")
            print(f"Project Status: {escrow.contract.project.status}")
            
            return True
        else:
            print(f"[X] Callback failed: {message}")
            return False
            
    except Escrow.DoesNotExist:
        print(f"[X] Escrow not found for conversation ID: {conversation_id}")
        return False
    except Exception as e:
        print(f"[X] ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == '--simulate-callback':
        if len(sys.argv) < 3:
            print("Error: Conversation ID required")
            print("Usage: python test_release_simple.py --simulate-callback <conversation_id>")
            sys.exit(1)
        simulate_b2c_callback(sys.argv[2])
    else:
        escrow_id = sys.argv[1] if len(sys.argv) > 1 else None
        result = test_release(escrow_id)
        
        if result and result.get('success'):
            print(f"\n[OK] Release initiated successfully!")
            print(f"Conversation ID: {result['conversation_id']}")
            print(f"\nTo simulate callback, run:")
            print(f"python test_release_simple.py --simulate-callback {result['conversation_id']}")
