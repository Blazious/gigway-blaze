"""
Contract & Escrow Flow Diagnostic
Run: python manage.py shell < test_contract_flow.py
"""

import os
from core.models import Project, Contract, Escrow, CustomUser
from django.utils import timezone
from datetime import timedelta

print("=" * 70)
print("CONTRACT & ESCROW DEPOSIT FLOW DIAGNOSTIC")
print("=" * 70)

# Find recent projects with signed contracts
print("\n1. Projects with Signed Contracts:")
print("-" * 70)
try:
    signed_contracts = Contract.objects.filter(
        client_signature__isnull=False,
        freelancer_signature__isnull=False
    ).order_by('-created_at')[:5]
    
    if not signed_contracts.exists():
        print("   ℹ️  No signed contracts found")
    else:
        for contract in signed_contracts:
            project = contract.project
            escrow = Escrow.objects.filter(contract=contract).first()
            
            print(f"\n   📋 Project: {project.title[:40]}")
            print(f"      Project ID: {project.id}")
            print(f"      Budget: KES {project.budget}")
            print(f"      Client: {project.client.email}")
            print(f"      Freelancer: {project.freelancer.email if project.freelancer else 'N/A'}")
            print(f"      Contract Status: {contract.status}")
            print(f"      Both Signed: ✅ YES")
            
            if escrow:
                print(f"      Escrow Status: {escrow.status}")
                print(f"      Escrow Amount: KES {escrow.amount}")
                print(f"      Escrow ID: {escrow.id}")
            else:
                print(f"      Escrow Status: ❌ NO ESCROW CREATED YET")
                print(f"      👉 ACTION: Client needs to click 'Deposit KES {project.budget}' button")

except Exception as e:
    print(f"   ❌ Error: {e}")

# Check for incomplete contracts
print("\n\n2. Contracts Awaiting Signatures:")
print("-" * 70)
try:
    incomplete = Contract.objects.filter(
        status__in=['pending_signature']
    ).order_by('-created_at')[:3]
    
    if not incomplete.exists():
        print("   ✅ No incomplete contracts")
    else:
        for contract in incomplete:
            project = contract.project
            client_signed = bool(contract.client_signature)
            freelancer_signed = bool(contract.freelancer_signature)
            
            print(f"\n   📋 Project: {project.title[:40]}")
            print(f"      Client Signed: {'✅' if client_signed else '❌ NO'}")
            print(f"      Freelancer Signed: {'✅' if freelancer_signed else '❌ NO'}")
            print(f"      Status: {contract.status}")

except Exception as e:
    print(f"   ❌ Error: {e}")

# Check recent escrows
print("\n\n3. Recent Escrow Transactions:")
print("-" * 70)
try:
    recent_escrows = Escrow.objects.order_by('-created_at')[:5]
    
    if not recent_escrows.exists():
        print("   ℹ️  No escrow transactions yet")
    else:
        for i, escrow in enumerate(recent_escrows, 1):
            print(f"\n   {i}. Status: {escrow.status:12} | Amount: KES {escrow.amount:6.2f}")
            print(f"      Project: {escrow.contract.project.title[:40]}")
            print(f"      Client Phone: {escrow.contract.project.client.phone_number}")
            print(f"      Freelancer Phone: {escrow.contract.project.freelancer.phone_number if escrow.contract.project.freelancer else 'N/A'}")
            print(f"      STK Checkout ID: {escrow.mpesa_checkout_request_id if escrow.mpesa_checkout_request_id else 'None'}")
            print(f"      Deposit Receipt: {escrow.mpesa_receipt if escrow.mpesa_receipt else 'Pending'}")

except Exception as e:
    print(f"   ❌ Error: {e}")

# Check M-Pesa configuration
print("\n\n4. M-Pesa Configuration Check:")
print("-" * 70)
try:
    from django.conf import settings
    
    stk_shortcode = getattr(settings, 'MPESA_SHORTCODE', None)
    b2c_shortcode = getattr(settings, 'MPESA_B2C_SHORTCODE', None)
    callback_url = getattr(settings, 'MPESA_CALLBACK_URL', None)
    
    print(f"   STK Shortcode (Paybill): {stk_shortcode}")
    print(f"   B2C Shortcode: {b2c_shortcode}")
    print(f"   Callback URL: {callback_url}")
    
    if stk_shortcode and b2c_shortcode and callback_url:
        print(f"   ✅ All M-Pesa config values set")
    else:
        print(f"   ❌ Missing M-Pesa configuration")

except Exception as e:
    print(f"   ❌ Error: {e}")

# Troubleshooting guide
print("\n\n5. Troubleshooting Guide:")
print("-" * 70)
print("""
   If you don't see the "Deposit Funds to Escrow" form after both parties sign:

   A) Check if escrowStatus is stuck in a non-deposit state:
      - Browser Console → Type: localStorage.getItem('escrowStatus')
      - If status is 'held' or 'released' → Can't deposit (already paid)
      - If status is anything else → Contact support

   B) Check if both parties actually signed:
      - Look at database: Contract model should show both signatures
      - Run: from core.models import Contract; c = Contract.objects.last(); 
             print(c.client_signature, c.freelancer_signature)

   C) Check if you're logged in as the CLIENT:
      - Deposit form only shows for clients (isClient check)
      - If freelancer is viewing, they won't see deposit form

   D) Check for API errors:
      - Open DevTools (F12) → Network tab
      - Click "Deposit KES..." → Watch for failed requests
      - Check the response for error messages

   E) If M-Pesa STK push doesn't appear after clicking Deposit:
      - Check ngrok is running: ngrok status
      - Check .env MPESA_CALLBACK_URL is correct
      - Check Django logs for errors
      - Verify M-Pesa credentials are valid

   Next Step: 
   1. Identify which issue applies ↑
   2. Provide that info so we can fix the specific problem
""")

print("\n" + "=" * 70)
print("DIAGNOSTIC COMPLETE")
print("=" * 70)
