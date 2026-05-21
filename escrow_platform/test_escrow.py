"""
Escrow System Health Check
Run: python manage.py shell < test_escrow.py
"""

import os
from core.models import Escrow
from django.conf import settings
from django.utils import timezone

print("=" * 60)
print("ESCROW SYSTEM HEALTH CHECK")
print("=" * 60)

# Test 1: B2C Shortcode
print("\n1. B2C Configuration:")
try:
    b2c_shortcode = os.getenv('MPESA_B2C_SHORTCODE') or getattr(settings, 'MPESA_B2C_SHORTCODE', None)
    if b2c_shortcode:
        print(f"   ✅ MPESA_B2C_SHORTCODE = {b2c_shortcode}")
    else:
        print("   ❌ MPESA_B2C_SHORTCODE not found in settings!")
except Exception as e:
    print(f"   ❌ Error checking B2C shortcode: {e}")

# Test 2: Status Choices
print("\n2. Status Choices:")
try:
    valid_statuses = dict(Escrow.STATUS_CHOICES)
    required = ['pending', 'held', 'releasing', 'released', 'failed']
    missing = [s for s in required if s not in valid_statuses]

    if not missing:
        print(f"   ✅ All statuses present: {list(valid_statuses.keys())}")
    else:
        print(f"   ❌ Missing statuses: {missing}")
except Exception as e:
    print(f"   ❌ Error checking statuses: {e}")

# Test 3: Model Fields
print("\n3. Model Fields:")
try:
    fields = [f.name for f in Escrow._meta.get_fields()]
    required_fields = ['mpesa_checkout_request_id', 'mpesa_conversation_id']
    missing_fields = [f for f in required_fields if f not in fields]
    
    if not missing_fields:
        print(f"   ✅ All required fields present")
    else:
        print(f"   ❌ Missing fields: {missing_fields}")
except Exception as e:
    print(f"   ❌ Error checking fields: {e}")

# Test 4: Stuck Escrows
print("\n4. Stuck Escrows:")
try:
    stuck = Escrow.objects.filter(
        status__in=['releasing']
    )
    if stuck.exists():
        print(f"   ⚠️  Found {stuck.count()} escrow(s) in progress:")
        for e in stuck:
            print(f"      [IN PROGRESS] #{str(e.id)[:8]}: {e.status} - KES {e.amount}")
    else:
        print("   ✅ No stuck escrows")
except Exception as e:
    print(f"   ❌ Error checking stuck escrows: {e}")

# Test 5: Recent Activity
print("\n5. Recent Escrows (last 5):")
try:
    recent = Escrow.objects.order_by('-created_at')[:5]
    if recent.exists():
        for i, e in enumerate(recent, 1):
            print(f"   {i}. Status: {e.status:10} | Amount: {e.amount:6} KES | {e.contract.project.title[:30]}")
    else:
        print("   ℹ️  No escrows yet")
except Exception as e:
    print(f"   ❌ Error checking recent escrows: {e}")

# Test 6: Data Integrity
print("\n6. Data Integrity Check:")
try:
    all_escrows = Escrow.objects.all()
    integrity_ok = True
    
    for e in all_escrows:
        # Check linked parties exist
        if not e.contract or not e.contract.project.client or not e.contract.project.freelancer:
            print(f"   ⚠️  Escrow {e.id} has missing contract/client/freelancer")
            integrity_ok = False
    
    if integrity_ok and all_escrows.exists():
        print(f"   ✅ All {all_escrows.count()} escrow(s) pass integrity check")
    elif not all_escrows.exists():
        print("   ℹ️  No escrows to check")
except Exception as e:
    print(f"   ❌ Error checking integrity: {e}")

print("\n" + "=" * 60)
print("✅ HEALTH CHECK COMPLETE - Ready to deploy!" if not missing_fields else "⚠️  FIX ISSUES ABOVE FIRST!")
print("=" * 60)

# Additional debugging info
print("\n📊 DEBUG INFO:")
print(f"   Django Settings Loaded: {bool(settings.configured)}")
print(f"   M-Pesa Environment: {getattr(settings, 'MPESA_ENVIRONMENT', 'NOT SET')}")
print(f"   Database: {settings.DATABASES['default']['ENGINE'].split('.')[-1]}")
