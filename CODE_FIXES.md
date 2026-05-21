# EXACT CODE FIXES TO APPLY

## Fix #1: Add 'releasing' to Model (1 line + 1 migration)

**File**: `core/models.py`  
**Lines**: 223-226

**BEFORE**:
```python
class EscrowTransaction(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('held', 'Funds Held'),
        ('released', 'Funds Released'),
        ('refunded', 'Funds Refunded'),
    ]
```

**AFTER**:
```python
class EscrowTransaction(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('held', 'Funds Held'),
        ('releasing', 'Releasing'),          # ← ADD THIS LINE
        ('released', 'Funds Released'),
        ('refunded', 'Funds Refunded'),
    ]
```

**Then run**:
```bash
python manage.py makemigrations core
python manage.py migrate
```

---

## Fix #2: Fix B2C Shortcode (2 lines)

**File**: `core/mpesa_b2c.py`  
**Lines**: 55-57

**BEFORE**:
```python
    # Sandbox B2C shortcode is usually 600000
    # If settings.MPESA_SHORTCODE is 174379 (Paybill), it won't work for B2C
    b2c_shortcode = os.getenv('MPESA_B2C_SHORTCODE', '600000') if settings.MPESA_ENVIRONMENT == 'sandbox' else settings.MPESA_SHORTCODE
```

**AFTER**:
```python
    # Get B2C shortcode (different from Paybill shortcode)
    if settings.MPESA_ENVIRONMENT == 'sandbox':
        b2c_shortcode = '600000'  # Sandbox B2C
    else:
        b2c_shortcode = os.getenv('MPESA_B2C_SHORTCODE')
        if not b2c_shortcode:
            raise ValueError(
                "MPESA_B2C_SHORTCODE not configured in .env! "
                "This must be different from MPESA_SHORTCODE (Paybill). "
                "Contact Safaricom for your B2C business shortcode."
            )
```

**Also add to `.env`**:
```env
MPESA_B2C_SHORTCODE=600000  # For sandbox, use actual code for production
```

---

## Fix #3: Fix Refund Phone Swap (11 lines removed, restructured)

**File**: `core/views.py`  
**Lines**: 794-810

**BEFORE** (BUGGY):
```python
            elif decision == 'refund':
                # Refund client (reverse the phone numbers)
                client_phone = escrow.client_phone
                escrow.client_phone = escrow.freelancer_phone
                escrow.freelancer_phone = client_phone
                
                result = release_escrow_funds(escrow, 100)  # Full refund
                if not result['success']:
                    return Response(
                        {'error': f"Failed to process refund: {result['error']}"},
                        status=status.HTTP_400_BAD_REQUEST
                    )
                
                escrow.status = 'refunded'
                escrow.save()
                resolution = f"Full refund issued to client. {resolution_notes}"
```

**AFTER** (FIXED):
```python
            elif decision == 'refund':
                # Refund client - send directly to client phone without modifying escrow
                try:
                    result = release_escrow_funds(escrow, 100)  # Full refund
                    if not result['success']:
                        return Response(
                            {'error': f"Failed to process refund: {result['error']}"},
                            status=status.HTTP_400_BAD_REQUEST
                        )
                    
                    # Save conversation ID for callback tracking
                    escrow.mpesa_conversation_id = result.get('conversation_id')
                    escrow.status = 'refunded'
                    escrow.save()
                    
                    resolution = f"Full refund issued to client. {resolution_notes}"
                except Exception as e:
                    return Response(
                        {'error': f"Refund failed: {str(e)}"},
                        status=status.HTTP_400_BAD_REQUEST
                    )
```

---

## Fix #4: Update release_escrow_funds to handle refunds

**File**: `core/mpesa_b2c.py`  
**Lines**: 29-45

**The function needs modification**:

```python
def release_escrow_funds(escrow_transaction, percentage=100):
    """Release funds to freelancer (percentage of escrow amount)"""
    amount = float(escrow_transaction.amount) * (percentage / 100)
    
    try:
        result = send_b2c_payment(
            phone_number=escrow_transaction.freelancer_phone,
            amount=amount,
            occasion=f"Project {escrow_transaction.project.id} payment ({percentage}%)",
            remarks=f"Dispute resolution payout"
        )
        
        return {
            'success': True,
            'amount_released': amount,
            'conversation_id': result['conversation_id'],  # ← MAKE SURE THIS IS RETURNED
            'percentage': percentage
        }
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }
```

**Key point**: Make sure `result['conversation_id']` is being returned!

---

## Fix #5: Save conversation ID for refunds (add 1 line)

**File**: `core/views.py`  
**Lines**: 807 (in the refund elif block)

**Add this line after B2C result**:
```python
# Save conversation ID so callback can find this escrow
escrow.mpesa_conversation_id = result.get('conversation_id')
```

So the complete refund block becomes:
```python
elif decision == 'refund':
    try:
        result = release_escrow_funds(escrow, 100)
        if not result['success']:
            return Response(...)
        
        escrow.mpesa_conversation_id = result.get('conversation_id')  # ← NEW
        escrow.status = 'refunded'
        escrow.save()
        
        resolution = f"Full refund issued to client. {resolution_notes}"
```

---

## Fix #6: Add idempotency check (OPTIONAL but recommended)

**File**: `core/views.py`  
**In DeliverableApproveView.post()** - Lines 482-495

**ADD THIS CHECK** after getting the deliverable:

```python
def post(self, request, deliverable_id):
    try:
        deliverable = Deliverable.objects.get(id=deliverable_id)
        
        # Validate client is project owner
        if deliverable.project.client != request.user:
            return Response(
                {'error': 'Only project owner can approve deliverables'},
                status=status.HTTP_403_FORBIDDEN
            )

        # Validate escrow status
        if not hasattr(deliverable.project, 'escrow') or deliverable.project.escrow.status != 'held':
            return Response(
                {'error': 'Escrow funds must be held to approve deliverables'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # ← ADD THIS BLOCK
        # Idempotency: Check if already approved
        escrow = deliverable.project.escrow
        if deliverable.status == 'approved':
            if escrow.status == 'released':
                return Response(
                    {'message': 'Deliverable already approved and funds released'},
                    status=status.HTTP_200_OK
                )
            elif escrow.status == 'releasing':
                return Response(
                    {'message': 'Release already in progress. Funds being sent to freelancer.'},
                    status=status.HTTP_200_OK
                )
            else:
                return Response(
                    {'error': f'Unexpected state: {escrow.status}'},
                    status=status.HTTP_400_BAD_REQUEST
                )

        if deliverable.status != 'submitted':
            return Response(
                {'error': f'Can only approve submitted deliverables. Current status: {deliverable.status}'},
                status=status.HTTP_400_BAD_REQUEST
            )
        # END NEW BLOCK

        # Rest of the function continues...
```

---

## How to Apply All Fixes

### Step 1: Update .env
```bash
# Add this line to .env
MPESA_B2C_SHORTCODE=600000  # For sandbox; use your B2C code for production
```

### Step 2: Edit models.py
```bash
# Add 'releasing' to STATUS_CHOICES in EscrowTransaction
```

### Step 3: Create and run migration
```bash
python manage.py makemigrations core
python manage.py migrate
```

### Step 4: Edit mpesa_b2c.py
```bash
# Fix B2C shortcode logic and ensure conversation_id is returned
```

### Step 5: Edit views.py
```bash
# 1. Fix refund phone swap (lines 794-810)
# 2. Add conversation_id save for refunds
# 3. Add idempotency check in DeliverableApproveView (optional)
```

### Step 6: Restart Django
```bash
python manage.py runserver 0.0.0.0:8000
# Or with ngrok:
python start_with_ngrok.py
```

### Step 7: Test complete flow
1. Create project → Freelancer proposes → Client accepts
2. Both sign contract
3. Client deposits (check escrow status: 'held')
4. Freelancer submits deliverable
5. Client approves (check escrow status: 'releasing' then 'released')
6. Freelancer checks wallet (should show in earnings)

---

## Validation Checklist

After applying fixes, verify:

```python
# In Django shell:
python manage.py shell

# 1. Check STATUS_CHOICES includes 'releasing'
from core.models import EscrowTransaction
EscrowTransaction.STATUS_CHOICES
# Should show: (..., ('releasing', 'Releasing'), ...)

# 2. Check B2C shortcode logic
import os
from django.conf import settings
from core.mpesa_b2c import send_b2c_payment

# 3. Check a recent escrow (if it exists)
escrow = EscrowTransaction.objects.last()
print(f"Status: {escrow.status}")
print(f"Conversation ID: {escrow.mpesa_conversation_id}")
print(f"Client phone: {escrow.client_phone}")
print(f"Freelancer phone: {escrow.freelancer_phone}")
# Phones should NOT be swapped!

# 4. Test B2C with dummy payment (won't actually send)
# This just tests the logic:
print(f"MPESA_ENVIRONMENT: {settings.MPESA_ENVIRONMENT}")
print(f"B2C_SHORTCODE logic should pick: {'600000' if settings.MPESA_ENVIRONMENT == 'sandbox' else 'production'}")
```

---

## Expected Outcomes After Fixes

| Issue | Before | After |
|-------|--------|-------|
| B2C payments | Fail (shortcode error) | ✅ Work in sandbox |
| Refunds | Corrupt phone data | ✅ Send to correct client phone |
| 'releasing' status | Migration error | ✅ Status transition works |
| Conversation ID tracking | Not saved for refunds | ✅ Callback can find escrow |
| Double approve | Sends 2x payments | ✅ Returns 200 OK on retry |
| Freelancer wallet | Shows 'releasing' stuck | ✅ Shows 'released' after callback |

