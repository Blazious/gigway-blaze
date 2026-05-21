# Escrow Platform - Diagnostic Analysis

## Quick Answers to Your 4 Questions

### 1. **What specific actions are failing after deposit?**

After successful M-Pesa deposit (when escrow moves to `held` status):

- ✅ **Contract signing** - Works (model exists)
- ✅ **Deliverable submission** - Works  
- ⚠️ **Deliverable approval** → **Funds release** - PARTIALLY WORKS but has issues:
  - B2C payment is initiated
  - Escrow transitions to `releasing` state
  - **PROBLEM**: No confirmation that B2C callback succeeded before returning to client
  - **Status updates** after B2C callback depend entirely on callback firing

- ❌ **Dispute resolution refunds** - CRITICAL BUG (see below)
- ⚠️ **Status transitions** - Inconsistent state management

---

### 2. **What errors you'll likely see?**

#### **Silent Failures (Most Likely)**
- Client approves deliverable → gets "Funds being released" message
- Freelancer doesn't receive funds → stuck in waiting
- Escrow shows `releasing` status forever (callback never came back)

#### **B2C Payment Issues**
- `MPESA_B2C_SHORTCODE` mismatch: Sandbox = `600000`, but your settings might have `174379` (Paybill code - won't work for B2C)
- Callback URL unreachable by Safaricom
- Invalid phone format for freelancer

#### **Dispute Resolution Refund Bug** ⚠️ CRITICAL
```python
# Line 795-807 in views.py - BUGGY CODE:
if decision == 'refund':
    # Refund client (reverse the phone numbers)
    client_phone = escrow.client_phone
    escrow.client_phone = escrow.freelancer_phone
    escrow.freelancer_phone = client_phone
    
    result = release_escrow_funds(escrow, 100)  # Full refund
```
**THE PROBLEM**: 
- You're swapping phone numbers IN THE OBJECT
- Then calling `release_escrow_funds` which uses the MODIFIED `freelancer_phone`
- But then you try to SAVE the modified escrow with swapped phones
- Next time anyone checks escrow, phone numbers are permanently swapped!
- If called again, funds go to wrong person

---

### 3. **Your current M-Pesa setup**

Based on your code:

✅ **Using Daraja API (Safaricom)** - Confirmed in `mpesa_config.py`

✅ **STK Push for deposits** - Working:
- `initiate_stk_push()` called in `EscrowDepositView`
- Stores `mpesa_checkout_request_id`
- Callback updates status to `held`

⚠️ **B2C API for withdrawals** - Partially working but risky:
- `send_b2c_payment()` used for both:
  - Deliverable approval release
  - Dispute resolution (release or refund)
- **Issue**: `MPESA_B2C_SHORTCODE` might be wrong (check your `.env`)
- Callback stores `mpesa_conversation_id` and updates to `released`

⚠️ **Callback URLs** - Set up but with gaps:
- Deposit: `/api/mpesa/callback/deposit/` ✅
- Release: `/api/mpesa/callback/release/` ✅
- **ISSUE**: Callback expects `mpesa_conversation_id` but you might not be tracking it properly across all flows

---

### 4. **Your escrow transaction model**

```python
class EscrowTransaction(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),       # Initial state after proposal accepted
        ('held', 'Funds Held'),       # After M-Pesa deposit succeeds
        ('released', 'Funds Released'),  # After B2C to freelancer succeeds
        ('refunded', 'Funds Refunded'),  # After refund to client
        # MISSING: 'releasing' - used but not defined!
    ]

    id = UUIDField(primary_key)
    project = OneToOneField(Project)  # ✅ Good - one escrow per project
    client_phone = CharField()        # ✅ Track client
    freelancer_phone = CharField()    # ✅ Track freelancer
    amount = DecimalField()           # ✅ Track amount
    status = CharField()              # ⚠️ See issues below
    
    # M-Pesa tracking
    mpesa_deposit_receipt = CharField()         # ✅ Deposit receipt
    mpesa_release_receipt = CharField()         # ✅ Release receipt
    mpesa_checkout_request_id = CharField()     # ✅ STK tracking
    mpesa_conversation_id = CharField()         # ⚠️ Used but not set in deliverable approve!
    
    deposited_at = DateTimeField()      # ✅
    released_at = DateTimeField()       # ✅
    created_at = DateTimeField()        # ✅
```

**Relationship Map:**
```
CustomUser (Client)
    ↓
Project (budget amount)
    ↓
EscrowTransaction (holds client_phone, freelancer_phone, amount)
    ↓
Contract (pending → signed → active)
    ↓
Deliverable (submitted → approved)
    ↓
M-Pesa B2C Release → Funds to freelancer
```

---

## Critical Issues Found

### 🔴 **Issue 1: Dispute Refund Phone Swap Bug**
**Location**: [views.py lines 794-807](views.py#L794-L807)

**Problem**: Permanently swaps phone numbers in escrow, corrupting data

**Fix**: Use separate variables for B2C payment direction

---

### 🔴 **Issue 2: B2C Shortcode Mismatch (Likely)**
**Location**: [mpesa_b2c.py line 57](mpesa_b2c.py#L57)

**Current code**:
```python
b2c_shortcode = os.getenv('MPESA_B2C_SHORTCODE', '600000') if settings.MPESA_ENVIRONMENT == 'sandbox' else settings.MPESA_SHORTCODE
```

**Problem**: For refunds, you need a `BusinessPayment` shortcode (600000 in sandbox), but your production `MPESA_SHORTCODE` might be a Paybill (174379), which doesn't work for B2C

---

### 🟡 **Issue 3: Missing `releasing` status in model**
**Location**: [models.py line 223](models.py#L223)

You use `status = 'releasing'` but it's not in `STATUS_CHOICES`:
- [views.py line 527](views.py#L527) - deliverable approve
- [views.py line 791](views.py#L791) - dispute release

Database migration will fail if this isn't declared

---

### 🟡 **Issue 4: Conversation ID not set in deliverable approval**
**Location**: [views.py lines 515-519](views.py#L515-L519)

```python
payment_result = send_b2c_payment(...)
escrow.mpesa_conversation_id = payment_result['conversation_id']  # ✅ This line exists
escrow.status = 'releasing'
escrow.save()
```

Actually this looks correct. The issue is the callback must be able to find the escrow by this ID.

---

### 🟡 **Issue 5: No state machine validation**
The code allows invalid state transitions:
- Can approve deliverable multiple times?
- Can resolve dispute after already released?
- No idempotency checks

---

## Data Flow Summary

```
1. Freelancer accepted → Escrow created (status: pending)
2. Contract signed → Ready for deposit
3. Client deposits → initiate_stk_push() called
   └─ Safaricom calls /api/mpesa/callback/deposit/
   └─ Escrow → held ✅
   
4. Deliverable submitted
5. Client approves → send_b2c_payment() called
   └─ Safaricom calls /api/mpesa/callback/release/
   └─ Escrow → released ✅ (hopefully)
   
6. Freelancer checks wallet
   └─ Sums up 'released' status escrows ✅
```

---

## Next Steps for Fixes

1. **Add `releasing` to model STATUS_CHOICES** (1 line)
2. **Fix refund phone swap** (3 lines)
3. **Verify B2C shortcode in .env** (1 line in .env)
4. **Ensure callback URLs are reachable** (infrastructure)
5. **Add idempotency checks** (middleware/decorators)
6. **Add state machine validation** (method in model)

