#!/usr/bin/env python
"""
Complete Escrow Workflow Test Script
Tests the full M-Pesa escrow flow from backend without frontend
"""
import os
import sys
import django
import requests
import json
from datetime import datetime, timedelta

# Setup Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'escrow_platform.settings')
django.setup()

from django.contrib.auth import get_user_model
from core.models import Project, Proposal, Contract, Escrow, Deliverable
from core.mpesa_stk import initiate_stk_push, format_phone_number
from core.mpesa_callbacks import process_deposit_callback, process_b2c_callback
from django.utils import timezone

User = get_user_model()

# Colors for output
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    RESET = '\033[0m'
    BOLD = '\033[1m'

def print_step(step_num, description):
    print(f"\n{Colors.BOLD}{Colors.BLUE}=== STEP {step_num}: {description} ==={Colors.RESET}")

def print_success(message):
    print(f"{Colors.GREEN}✓ {message}{Colors.RESET}")

def print_error(message):
    print(f"{Colors.RED}✗ {message}{Colors.RESET}")

def print_info(message):
    print(f"{Colors.YELLOW}ℹ {message}{Colors.RESET}")

def print_data(data):
    print(f"{Colors.YELLOW}{json.dumps(data, indent=2, default=str)}{Colors.RESET}")

def test_full_workflow():
    """Test the complete escrow workflow"""
    
    print(f"\n{Colors.BOLD}{'='*60}")
    print("M-PESA ESCROW WORKFLOW TEST")
    print(f"{'='*60}{Colors.RESET}\n")
    
    # Test data
    client_email = f"test_client_{datetime.now().strftime('%Y%m%d%H%M%S')}@test.com"
    freelancer_email = f"test_freelancer_{datetime.now().strftime('%Y%m%d%H%M%S')}@test.com"
    client_phone = input(f"\n{Colors.YELLOW}Enter CLIENT phone number (e.g., 254712345678): {Colors.RESET}").strip()
    freelancer_phone = input(f"{Colors.YELLOW}Enter FREELANCER phone number (e.g., 254798765432): {Colors.RESET}").strip()
    
    # Format phone numbers
    client_phone = format_phone_number(client_phone)
    freelancer_phone = format_phone_number(freelancer_phone)
    
    print_info(f"Client Phone: {client_phone}")
    print_info(f"Freelancer Phone: {freelancer_phone}")
    
    try:
        # STEP 1: Create Client User
        print_step(1, "Creating Client User")
        try:
            client = User.objects.get(email=client_email)
            print_info("Client already exists, using existing")
        except User.DoesNotExist:
            client = User.objects.create_user(
                email=client_email,
                password="testpass123",
                phone_number=client_phone,
                user_type='client'
            )
            print_success(f"Client created: {client.email}")
        
        # STEP 2: Create Freelancer User
        print_step(2, "Creating Freelancer User")
        try:
            freelancer = User.objects.get(email=freelancer_email)
            print_info("Freelancer already exists, using existing")
        except User.DoesNotExist:
            freelancer = User.objects.create_user(
                email=freelancer_email,
                password="testpass123",
                phone_number=freelancer_phone,
                user_type='freelancer'
            )
            print_success(f"Freelancer created: {freelancer.email}")
        
        # STEP 3: Create Project
        print_step(3, "Creating Project")
        project = Project.objects.create(
            client=client,
            title="Test Escrow Project",
            description="Testing the escrow workflow",
            scope_of_work="Complete testing of escrow feature",
            timeline=timezone.now().date() + timedelta(days=7),
            budget=100.00,
            status='open'
        )
        print_success(f"Project created: {project.title} (ID: {project.id})")
        print_data({
            'id': str(project.id),
            'title': project.title,
            'budget': str(project.budget),
            'status': project.status
        })
        
        # STEP 4: Create Proposal
        print_step(4, "Creating Proposal")
        proposal, created = Proposal.objects.get_or_create(
            project=project,
            freelancer=freelancer,
            defaults={
                'cover_letter': 'I can complete this project',
                'bid_amount': 100.00,
                'status': 'pending'
            }
        )
        if created:
            print_success(f"Proposal created by {freelancer.email}")
        else:
            print_info("Proposal already exists")
        
        # STEP 5: Accept Proposal (Creates Contract & Escrow)
        print_step(5, "Accepting Proposal")
        proposal.status = 'accepted'
        proposal.save()
        
        project.status = 'assigned'
        project.freelancer = freelancer
        project.save()
        
        # Generate contract
        from core.contract_generator import generate_contract_text
        contract, created = Contract.objects.get_or_create(
            project=project,
            defaults={
                'contract_text': generate_contract_text(project),
                'status': 'pending'
            }
        )
        if created:
            print_success("Contract created")
        else:
            print_info("Contract already exists")
        
        # Create escrow (linked to contract)
        escrow, created = Escrow.objects.get_or_create(
            contract=contract,
            defaults={
                'amount': project.budget,
                'status': 'pending'
            }
        )
        if created:
            print_success("Escrow transaction created")
            print_data({
                'escrow_id': str(escrow.id),
                'client_phone': client_phone,
                'freelancer_phone': freelancer_phone,
                'amount': str(escrow.amount),
                'status': escrow.status
            })
        else:
            print_info("Escrow already exists")
            print_data({
                'escrow_id': str(escrow.id),
                'status': escrow.status
            })
        
        # STEP 6: Sign Contract (Both Parties)
        print_step(6, "Signing Contract (Both Parties)")
        
        # Client signs
        contract.client_signature = f"client_signature_{datetime.now().timestamp()}"
        contract.client_signed_at = timezone.now()
        contract.save()
        print_success("Client signed contract")
        
        # Freelancer signs
        contract.freelancer_signature = f"freelancer_signature_{datetime.now().timestamp()}"
        contract.freelancer_signed_at = timezone.now()
        contract.status = 'signed'
        contract.save()
        print_success("Freelancer signed contract")
        print_success("Contract fully signed!")
        
        # STEP 7: Initiate Deposit
        print_step(7, "Initiating M-Pesa Deposit (STK Push)")
        print_info(f"Amount: KES {project.budget}")
        print_info(f"Phone: {client_phone}")
        
        try:
            checkout_id = initiate_stk_push(
                phone_number=client_phone,
                amount=float(project.budget),
                account_reference=f"ESCROW-{project.id}",
                transaction_desc=f"Payment for {project.title}"
            )
            
            print_success(f"STK Push initiated successfully!")
            print_info(f"Checkout Request ID: {checkout_id}")
            
            # Update escrow with checkout ID
            escrow.mpesa_checkout_request_id = checkout_id
            escrow.status = 'pending'
            escrow.save()
            
            print_info("\n" + "="*60)
            print_info("ACTION REQUIRED: Check your phone and complete the M-Pesa payment!")
            print_info("="*60)
            
            # Wait for user to complete payment
            input(f"\n{Colors.YELLOW}Press ENTER after completing the M-Pesa payment on your phone...{Colors.RESET}")
            
        except Exception as e:
            print_error(f"Failed to initiate STK Push: {str(e)}")
            import traceback
            traceback.print_exc()
            return False
        
        # STEP 8: Simulate Callback (for testing - in production this comes from Safaricom)
        print_step(8, "Simulating M-Pesa Callback")
        print_info("In production, Safaricom sends this callback automatically")
        print_info("For testing, we'll simulate a successful callback")
        
        # Ask user if payment was successful
        success = input(f"\n{Colors.YELLOW}Did the payment succeed? (y/n): {Colors.RESET}").strip().lower()
        
        if success == 'y':
            # Simulate successful callback
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
                print_success(f"Callback processed: {message}")
                
                # Refresh escrow from DB
                escrow.refresh_from_db()
                print_data({
                    'escrow_id': str(escrow.id),
                    'status': escrow.status,
                    'deposit_receipt': escrow.mpesa_receipt
                })
                
                # Check project status
                project.refresh_from_db()
                print_info(f"Project status: {project.status}")
                
            else:
                print_error(f"Callback processing failed: {message}")
                return False
        else:
            print_info("Skipping callback simulation (payment not completed)")
            return False
        
        # STEP 9: Verify Escrow Status
        print_step(9, "Verifying Escrow Status")
        escrow.refresh_from_db()
        print_data({
            'escrow_id': str(escrow.id),
            'status': escrow.status,
            'amount': str(escrow.amount),
            'client_phone': client_phone,
            'freelancer_phone': freelancer_phone,
            'deposit_receipt': escrow.mpesa_receipt
        })
        
        if escrow.status == 'held':
            print_success("✓ Escrow funds are HELD successfully!")
        else:
            print_error(f"✗ Escrow status is '{escrow.status}' (expected 'held')")
            return False
        
        # STEP 10: Test Release Flow (Optional)
        print_step(10, "Testing Release Flow (Optional)")
        release = input(f"\n{Colors.YELLOW}Do you want to test the release flow? (y/n): {Colors.RESET}").strip().lower()
        
        if release == 'y':
            print_info("Creating a deliverable...")
            deliverable = Deliverable.objects.create(
                contract=contract,
                file_paths="test_file.pdf",
                description="Test deliverable",
                status='submitted'
            )
            print_success("Deliverable created")
            
            print_info("Approving deliverable (this triggers B2C payment)...")
            from core.mpesa_b2c import send_b2c_payment
            
            try:
                payment_result = send_b2c_payment(
                    phone_number=contract.project.freelancer.phone_number,
                    amount=float(escrow.amount),
                    occasion=f"Payment for {project.title}",
                    remarks="Freelancer payment via escrow"
                )
                
                print_success(f"B2C payment initiated!")
                print_info(f"Conversation ID: {payment_result['conversation_id']}")
                
                escrow.mpesa_conversation_id = payment_result['conversation_id']
                escrow.status = 'releasing'
                escrow.save()
                
                print_info("\n" + "="*60)
                print_info("B2C payment sent! Check freelancer's phone.")
                print_info("="*60)
                
                # Simulate B2C callback
                input(f"\n{Colors.YELLOW}Press ENTER after checking B2C payment status...{Colors.RESET}")
                success_b2c = input(f"{Colors.YELLOW}Did B2C payment succeed? (y/n): {Colors.RESET}").strip().lower()
                
                if success_b2c == 'y':
                    b2c_callback = json.dumps({
                        "Result": {
                            "ConversationID": payment_result['conversation_id'],
                            "ResultCode": 0,
                            "ResultDesc": "The service request is processed successfully.",
                            "ResultParameters": {
                                "ResultParameter": [
                                    {"Key": "TransactionReceipt", "Value": f"B2C{datetime.now().strftime('%Y%m%d%H%M%S')}"},
                                    {"Key": "TransactionAmount", "Value": str(int(escrow.amount))},
                                    {"Key": "B2CWorkingAccountAvailableFunds", "Value": "100000"},
                                    {"Key": "B2CUtilityAccountAvailableFunds", "Value": "50000"},
                                    {"Key": "TransactionCompletedDateTime", "Value": datetime.now().strftime('%Y.%m.%d %H:%M:%S')},
                                    {"Key": "ReceiverPartyPublicName", "Value": f"{freelancer_phone}"},
                                    {"Key": "B2CChargesPaidAccountAvailableFunds", "Value": "0"},
                                    {"Key": "B2CRecipientIsRegisteredCustomer", "Value": "Y"}
                                ]
                            }
                        }
                    })
                    
                    success, message = process_b2c_callback(b2c_callback.encode('utf-8'))
                    
                    if success:
                        print_success(f"B2C callback processed: {message}")
                        escrow.refresh_from_db()
                        print_data({
                            'escrow_id': str(escrow.id),
                            'status': escrow.status,
                            'release_receipt': escrow.mpesa_release_receipt,
                            'released_at': escrow.released_at
                        })
                    else:
                        print_error(f"B2C callback failed: {message}")
                
            except Exception as e:
                print_error(f"B2C payment failed: {str(e)}")
                import traceback
                traceback.print_exc()
        
        # Final Summary
        print(f"\n{Colors.BOLD}{'='*60}")
        print("TEST SUMMARY")
        print(f"{'='*60}{Colors.RESET}\n")
        
        escrow.refresh_from_db()
        project.refresh_from_db()
        
        print_data({
            'project_id': str(project.id),
            'project_status': project.status,
            'escrow_id': str(escrow.id),
            'escrow_status': escrow.status,
            'amount': str(escrow.amount),
            'deposit_receipt': escrow.mpesa_receipt,
            'release_receipt': escrow.mpesa_release_receipt
        })
        
        if escrow.status in ['held', 'released', 'refunded']:
            print_success("\n✓ ESCROW WORKFLOW TEST COMPLETED SUCCESSFULLY!")
        else:
            print_error(f"\n✗ Escrow status is '{escrow.status}' - workflow may not be complete")
        
        return True
        
    except Exception as e:
        print_error(f"Test failed with error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    print(f"\n{Colors.BOLD}M-Pesa Escrow Workflow Test Script{Colors.RESET}")
    print("This script tests the complete escrow workflow from backend")
    print("Make sure your Django server is running and M-Pesa credentials are configured\n")
    
    proceed = input(f"{Colors.YELLOW}Continue? (y/n): {Colors.RESET}").strip().lower()
    if proceed == 'y':
        test_full_workflow()
    else:
        print_info("Test cancelled")
