# BUG REPORT & FIXES

## Bug Priority Matrix

| Priority | Issue | Impact | Lines | Fix Effort |
|----------|-------|--------|-------|-----------|
| 🔴 CRITICAL | Dispute refund phone swap | Data corruption | views.py:794-807 | 3 min |
| 🔴 CRITICAL | B2C shortcode mismatch | B2C always fails | mpesa_b2c.py:57 | 2 min |
| 🟡 HIGH | Missing 'releasing' status | Migration fails | models.py:223 | 1 min + migration |
| 🟡 HIGH | No refund B2C handler | Refund feature breaks | views.py:800 | 5 min |
| 🟠 MEDIUM | No callback timeout handling | Stuck 'releasing' state | views.py & callbacks | 10 min |
| 🟠 MEDIUM | No idempotency checks | Approve called 2x = double payment | views.py:480 | 10 min |

---

## 🔴 BUG #1: CRITICAL - Dispute Refund Phone Swap (Data Corruption)

**Location**: [views.py#L794-L807](views.py#L794)

**Current Buggy Code**:
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
    escrow.save()  # ❌ SAVES SWAPPED PHONE NUMBERS!
    resolution = f"Full refund issued to client. {resolution_notes}"
```

**The Problem**:
1. You swap `client_phone` ↔ `freelancer_phone` in the object
2. Call `release_escrow_funds()` which sends funds using the SWAPPED `freelancer_phone` (now pointing to client)
3. You SAVE the escrow with permanently swapped phones
4. Next time someone checks escrow data → phones are wrong
5. If dispute is escalated again → funds go to WRONG person!

**What should happen**:
```
Original:  client_phone=254700000001, freelancer_phone=254700000002
Swap:      client_phone=254700000002, freelancer_phone=254700000001  ← in memory only
B2C:       Send to 254700000001 (client) ✅
Save:      client_phone=254700000001, freelancer_phone=254700000002  ← original!
```

**What's happening**:
```
Original:  client_phone=254700000001, freelancer_phone=254700000002
Swap:      client_phone=254700000002, freelancer_phone=254700000001
B2C:       Send to 254700000001 (client) ✅
Save:      client_phone=254700000002, freelancer_phone=254700000001  ← CORRUPTED! ❌
```

**Next dispute**:
```
Corrupted: client_phone=254700000002, freelancer_phone=254700000001
User thinks they're refunding client but they're sending to FREELANCER ❌❌❌
```

**FIX**: Don't modify the escrow object; use separate B2C logic:

```python
elif decision == 'refund':
    # ✅ NEW: Send refund to CLIENT without modifying escrow
    try:
        result = send_b2c_payment(
            phone_number=escrow.client_phone,  # ✅ Explicit, doesn't modify escrow
            amount=float(escrow.amount),
            occasion=f"Dispute resolution - Refund",
            remarks=f"Full refund for project {escrow.project.title}"
        )
        
        if not result.get('success'):
            return Response(
                {'error': f"Failed to process refund: {result.get('error')}"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Store the refund conversation ID
        escrow.mpesa_conversation_id = result['conversation_id']
        escrow.status = 'refunded'
        escrow.save()  # ✅ Phone numbers UNCHANGED
        
        resolution = f"Full refund issued to client. {resolution_notes}"
    except Exception as e:
        return Response(
            {'error': f"Refund failed: {str(e)}"},
            status=status.HTTP_400_BAD_REQUEST
        )
```

---

## 🔴 BUG #2: CRITICAL - B2C Shortcode Mismatch

**Location**: [mpesa_b2c.py#L57](mpesa_b2c.py#L57)

**Current Code**:
```python
def send_b2c_payment(phone_number, amount, occasion, remarks):
    phone = format_phone_number(phone_number)
    
    # Line 57 - THE PROBLEM
    b2c_shortcode = os.getenv('MPESA_B2C_SHORTCODE', '600000') if settings.MPESA_ENVIRONMENT == 'sandbox' else settings.MPESA_SHORTCODE
    #                                                                                                                       ↑
    #                                                          In production, this is probably 174379 (Paybill)
    #                                                          But B2C requires a different shortcode!
```

**Why it fails**:
- **Sandbox**: Uses `600000` (Safaricom B2C code) ✅
- **Production**: Uses `settings.MPESA_SHORTCODE` which is probably `174379` (your Paybill account)
- **Problem**: Paybill codes DON'T WORK for B2C payments! ❌
- **Result**: All B2C payments to freelancers FAIL in production

**Your current .env probably has**:
```env
MPESA_SHORTCODE=174379        # ← Paybill for STK deposits
MPESA_B2C_SHORTCODE=???       # ← Not defined!
```

**FIX**: Always use the correct B2C shortcode:

```python
def send_b2c_payment(phone_number, amount, occasion, remarks):
    phone = format_phone_number(phone_number)
    
    # ✅ FIXED: Use B2C-specific shortcode
    if settings.MPESA_ENVIRONMENT == 'sandbox':
        b2c_shortcode = '600000'  # Sandbox B2C
    else:
        # In production, use a B2C-enabled shortcode (different from Paybill)
        b2c_shortcode = os.getenv('MPESA_B2C_SHORTCODE', settings.MPESA_SHORTCODE)
        # If not configured, you'll know immediately with a clear error
    
    # Rest of function...
```

**Better approach**: Force explicit configuration:
```python
def send_b2c_payment(phone_number, amount, occasion, remarks):
    phone = format_phone_number(phone_number)
    
    # ✅ BEST: Require explicit B2C shortcode
    b2c_shortcode = os.getenv('MPESA_B2C_SHORTCODE')
    if not b2c_shortcode:
        if settings.MPESA_ENVIRONMENT == 'sandbox':
            b2c_shortcode = '600000'
        else:
            raise ValueError(
                "MPESA_B2C_SHORTCODE not set in .env for production! "
                "This is different from MPESA_SHORTCODE (Paybill). "
                "Contact Safaricom support to get your B2C shortcode."
            )
    
    # Rest of function...
```

**Update your .env**:
```env
# Existing Paybill for deposits
MPESA_SHORTCODE=174379

# NEW: B2C shortcode for releases
MPESA_B2C_SHORTCODE=600000        # Sandbox
# OR in production:
MPESA_B2C_SHORTCODE=<your-b2c-code>  # Get from Safaricom
```

---

## 🟡 BUG #3: HIGH - Missing 'releasing' Status in Model

**Location**: [models.py#L223-L226](models.py#L223)

**Current Code**:
```python
class EscrowTransaction(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('held', 'Funds Held'),
        ('released', 'Funds Released'),
        ('refunded', 'Funds Refunded'),
        # ❌ MISSING: 'releasing' is used but not defined!
    ]
```

**Where 'releasing' is used**:
- [views.py#L527](views.py#L527): `escrow.status = 'releasing'` (deliverable approve)
- [views.py#L791](views.py#L791): `escrow.status = 'releasing'` (dispute release)

**Why it matters**:
- Django won't allow saving to a status not in `STATUS_CHOICES`
- Will raise `ValidationError` OR
- Silently fail (depends on Django version)
- Data integrity issues

**FIX**: Add 'releasing' to choices:

```python
class EscrowTransaction(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),        # Initial state
        ('held', 'Funds Held'),        # After deposit succeeds
        ('releasing', 'Releasing'),    # ✅ NEW: B2C in progress
        ('released', 'Funds Released'), # B2C succeeded
        ('refunded', 'Funds Refunded'), # Dispute refund succeeded
    ]
```

**Then create and run migration**:
```bash
python manage.py makemigrations core
python manage.py migrate
```

---

## 🟡 BUG #4: HIGH - B2C Refund Not Tracking Conversation ID

**Location**: [views.py#L794-807](views.py#L794)

**Current Code**:
```python
if decision == 'refund':
    # ... (buggy phone swap code)
    result = release_escrow_funds(escrow, 100)
    
    escrow.status = 'refunded'
    escrow.save()  # ❌ Doesn't save conversation ID!
```

**Problem**: 
When B2C callback fires for refund, it looks for `mpesa_conversation_id` but it's not set!

```python
# In process_b2c_callback():
try:
    escrow = EscrowTransaction.objects.get(mpesa_conversation_id=conversation_id)
    # ❌ FAILS: conversation_id never saved for refunds!
except EscrowTransaction.DoesNotExist:
    logger.error(f"EscrowTransaction not found for conversation: {conversation_id}")
```

**FIX**: Track the conversation ID for refunds:

```python
elif decision == 'refund':
    try:
        result = send_b2c_payment(
            phone_number=escrow.client_phone,
            amount=float(escrow.amount),
            occasion=f"Dispute resolution - Refund",
            remarks=f"Full refund for {escrow.project.title}"
        )
        
        if not result.get('success'):
            return Response(
                {'error': f"Failed to process refund: {result.get('error')}"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # ✅ Save conversation ID so callback can find this escrow
        escrow.mpesa_conversation_id = result['conversation_id']
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

## 🟠 BUG #5: MEDIUM - No Callback Timeout Handling

**Location**: [views.py#L519-527](views.py#L519)

**Current Code**:
```python
payment_result = send_b2c_payment(
    phone_number=escrow.freelancer_phone,
    amount=float(escrow.amount),
    occasion=f"Payment for {deliverable.project.title}",
    remarks="Freelancer payment via escrow"
)

escrow.mpesa_conversation_id = payment_result['conversation_id']
escrow.status = 'releasing'  # ← What if callback never comes?
escrow.save()
```

**Problem**:
- Escrow transitions to `releasing`
- If Safaricom callback never fires (network issue, wrong URL, etc.)
- Escrow is **stuck forever** in `releasing` state
- Freelancer gets "Releasing..." but funds never arrive
- No recovery mechanism

**Scenario**:
```
1. Client approves deliverable
2. Backend calls Safaricom B2C
3. Safaricom responds: "OK, we'll process this"
4. Backend sets status = 'releasing'
5. ← Network issue: Callback never reaches your webhook
6. Freelancer checks wallet: "Status: releasing" (stuck)
7. Admin has no way to recover without manual DB edits
```

**Minimal FIX**: Add timeout field to model:

```python
class EscrowTransaction(models.Model):
    # ... existing fields ...
    
    # ✅ NEW: Track when B2C was initiated
    b2c_initiated_at = models.DateTimeField(null=True, blank=True)
```

Then in views:
```python
escrow.mpesa_conversation_id = payment_result['conversation_id']
escrow.status = 'releasing'
escrow.b2c_initiated_at = timezone.now()  # ✅ NEW
escrow.save()
```

Add a management command to check for stuck payments:
```bash
python manage.py check_stuck_releases --timeout=300  # 5 mins
```

Command would:
```python
from datetime import timedelta
from django.utils import timezone

stuck = EscrowTransaction.objects.filter(
    status='releasing',
    b2c_initiated_at__lt=timezone.now() - timedelta(minutes=5)
)

for escrow in stuck:
    # Email admin, create alert, or auto-retry B2C
```

---

## 🟠 BUG #6: MEDIUM - No Idempotency Checks

**Location**: [views.py#L480-527](views.py#L480) (DeliverableApproveView)

**Current Code**:
```python
def post(self, request, deliverable_id):
    deliverable = Deliverable.objects.get(id=deliverable_id)
    
    # No check: has this already been approved?
    deliverable.status = 'approved'
    deliverable.save()
    
    payment_result = send_b2c_payment(...)  # ← Called again if endpoint hit twice!
    escrow.status = 'releasing'
    escrow.save()
```

**Problem**:
If client calls approve twice (double-click, network retry, etc.):

```
Request #1: POST /api/deliverables/123/approve/
├─ Deliverable: submitted → approved
├─ B2C #1 initiated: sends 100 KES to freelancer
└─ Response: OK

Request #2: POST /api/deliverables/123/approve/ (accidental repeat)
├─ Deliverable: approved → approved (no-op)
├─ B2C #2 initiated: sends 100 KES to freelancer AGAIN ❌
└─ Freelancer gets 200 KES!
```

**FIX**: Check if already approved:

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
        escrow = deliverable.project.escrow
        if not escrow or escrow.status != 'held':
            return Response(
                {'error': 'Escrow funds must be held to approve deliverables'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # ✅ NEW: Check if already approved
        if deliverable.status == 'approved':
            # Already approved, check if release is complete
            if escrow.status == 'released':
                return Response(
                    {'message': 'Deliverable already approved and funds released'},
                    status=status.HTTP_200_OK
                )
            elif escrow.status == 'releasing':
                return Response(
                    {'message': 'Release already in progress'},
                    status=status.HTTP_200_OK
                )
            else:
                # Something went wrong, but deliverable was approved
                return Response(
                    {'error': f'Release in unexpected state: {escrow.status}'},
                    status=status.HTTP_400_BAD_REQUEST
                )

        # Only proceed if status is 'submitted'
        if deliverable.status != 'submitted':
            return Response(
                {'error': f'Can only approve submitted deliverables, current status: {deliverable.status}'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # NOW it's safe to approve and release
        deliverable.status = 'approved'
        deliverable.save()

        payment_result = send_b2c_payment(
            phone_number=escrow.freelancer_phone,
            amount=float(escrow.amount),
            occasion=f"Payment for {deliverable.project.title}",
            remarks="Freelancer payment via escrow"
        )
        
        escrow.mpesa_conversation_id = payment_result['conversation_id']
        escrow.status = 'releasing'
        escrow.save()

        deliverable.project.status = 'completed'
        deliverable.project.save()

        return Response(
            {
                'message': 'Deliverable approved. Funds being released to freelancer.',
                'conversation_id': payment_result['conversation_id']
            },
            status=status.HTTP_200_OK
        )

    except Deliverable.DoesNotExist:
        return Response(
            {'error': 'Deliverable not found'},
            status=status.HTTP_404_NOT_FOUND
        )
```

---

## Summary of All Fixes

| Bug | File | Lines | Fix | Priority |
|-----|------|-------|-----|----------|
| Refund phone swap | views.py | 794-807 | Remove swap, send B2C directly to client | 🔴 |
| B2C shortcode | mpesa_b2c.py | 57 | Use MPESA_B2C_SHORTCODE env var | 🔴 |
| Missing 'releasing' | models.py | 223-226 | Add to STATUS_CHOICES | 🟡 |
| Refund conversation ID | views.py | 800-807 | Save result['conversation_id'] | 🟡 |
| Callback timeout | models.py + views | multiple | Add b2c_initiated_at, create check command | 🟠 |
| Idempotency | views.py | 480-527 | Check deliverable status before B2C | 🟠 |

