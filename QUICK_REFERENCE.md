# Quick Reference - What's Failing

## Immediate Questions Answered

### 1️⃣ What specific actions are failing after deposit?

**After M-Pesa deposit succeeds** (escrow status → `held`):

| Action | Status | Issue |
|--------|--------|-------|
| Deliverable submission | ✅ Works | None |
| Deliverable approval | ⚠️ Partially | B2C initiated but no guarantee |
| Funds to freelancer | ❌ Likely Failing | B2C shortcode mismatch |
| Dispute resolution (release) | ⚠️ Partially | B2C issue + conversation ID not tracked |
| Dispute resolution (refund) | 🔴 BROKEN | Phone swap corrupts data |
| Freelancer receives payment | ❌ 80% chance failing | B2C shortcode |
| Wallet shows earnings | ❌ Can't reach "released" | If B2C fails |

**Root cause**: B2C payments are likely failing silently.

---

### 2️⃣ What errors are you seeing?

**Most likely errors you'll see**:

```
# In Django logs:
❌ B2C Request failed: {"ResultCode": 500, "ResultDesc": "Invalid shortcode"}
   → Cause: MPESA_SHORTCODE is Paybill (174379), not B2C code

❌ EscrowTransaction not found for conversation: AG_...
   → Cause: Refund doesn't save conversation_id

✓ No errors but nothing happens (Silent failure)
   → Cause: Callback URL unreachable by Safaricom
   → Cause: B2C shortcode mismatch

✓ Phone numbers swapped in database
   → Cause: Dispute refund bug (repeated refunds go to wrong person)
```

**Check your logs**:
```bash
# In escrow_platform directory:
tail -f error.log
tail -f mpesa_debug.log  # M-Pesa raw callbacks
```

---

### 3️⃣ Your current M-Pesa setup

**STK Push (Deposits)** ✅ WORKING
```
Client → phone → STK prompt → PIN → Safaricom
         ↓
      Callback fires → Escrow: held ✅
```

**B2C (Withdrawals)** ⚠️ LIKELY BROKEN
```
Freelancer ← phone ← B2C Payment ← FAILS
                     (shortcode wrong?)
         ↓
      Escrow stuck: releasing ❌
```

**Your .env is probably missing**:
```env
MPESA_B2C_SHORTCODE=600000     # ← This!
```

**Callback URLs** - Set correctly, but need ngrok:
```bash
cd escrow_platform
python start_with_ngrok.py  # Sets MPESA_CALLBACK_BASE_URL + updates .env
```

---

### 4️⃣ Your escrow transaction model

**Model structure**:
```python
EscrowTransaction
├── project (OneToOne)
├── client_phone (CharField)
├── freelancer_phone (CharField)
├── amount (DecimalField)
├── status (CharField) - pending → held → releasing → released
├── mpesa_deposit_receipt (for STK)
├── mpesa_release_receipt (for B2C)
├── mpesa_checkout_request_id (for STK tracking)
├── mpesa_conversation_id (for B2C tracking) ← Used for refund but not saved!
├── deposited_at
├── released_at
└── created_at
```

**Status transitions** (should be):
```
pending → held → releasing → released
              ↓
             refunded  (or back to pending if failed)
```

**Current problem**:
- `releasing` not in `STATUS_CHOICES` (will cause validation error)
- Refund doesn't save `conversation_id` (callback can't find it)
- Phone swap bug in refund logic

---

## The Data Flow (Current)

```
┌─ CLIENT DEPOSITS ─────────────────────────────────────────┐
│ POST /api/escrow/deposit/ with phone                       │
│                                                             │
│ 1. Check contract signed ✅                               │
│ 2. Create EscrowTransaction (status: pending)             │
│ 3. Call initiate_stk_push()                               │
│ 4. Save mpesa_checkout_request_id                         │
│                                                             │
│ ← M-Pesa STK appears on client phone                      │
│ ← Client enters PIN                                        │
│                                                             │
│ 5. Safaricom calls /api/mpesa/callback/deposit/  ✅       │
│    └─ Escrow status: pending → held                       │
└─────────────────────────────────────────────────────────────┘

┌─ FREELANCER SUBMITS DELIVERABLE ──────────────────────────┐
│ POST /api/deliverables/ with file + description           │
│                                                             │
│ 1. Create Deliverable (status: submitted)                │
│ 2. Check escrow is held ✅                                │
└─────────────────────────────────────────────────────────────┘

┌─ CLIENT APPROVES ─────────────────────────────────────────┐
│ POST /api/deliverables/123/approve/                       │
│                                                             │
│ 1. Update Deliverable: submitted → approved              │
│ 2. Call send_b2c_payment()                                │
│    ├─ Use shortcode (WRONG if production!) ❌             │
│    ├─ Send to freelancer_phone                           │
│    └─ Get conversation_id back                           │
│ 3. Save mpesa_conversation_id (if not refund) ✅          │
│ 4. Escrow status: held → releasing ⚠️                     │
│ 5. Project status: in_progress → completed               │
│                                                             │
│ ← Safaricom calls /api/mpesa/callback/release/  ⚠️        │
│    ├─ Find escrow by conversation_id ⚠️                   │
│    └─ Escrow status: releasing → released ✅             │
│                                                             │
│ ← Freelancer's phone gets M-Pesa deposit ✅ (if B2C OK)  │
└─────────────────────────────────────────────────────────────┘

┌─ FREELANCER CHECKS WALLET ────────────────────────────────┐
│ GET /api/wallet/                                           │
│                                                             │
│ 1. Sum all projects where freelancer assigned             │
│ 2. If escrow.status == 'released' → add to earnings ✅    │
│ 3. If escrow.status == 'held' → add to in_escrow ✅       │
│ 4. If escrow.status == 'releasing' → stuck ❌             │
└─────────────────────────────────────────────────────────────┘
```

---

## Issues by Severity

### 🔴 Will Definitely Break

**B2C Shortcode Issue**
```
Symptom: "Funds being released" message but freelancer never gets paid
Root cause: MPESA_SHORTCODE is 174379 (Paybill) but B2C needs different code
Fix: Add MPESA_B2C_SHORTCODE to .env
Impact: ALL freelancer withdrawals fail in production
```

**Refund Phone Swap Bug**
```
Symptom: After refund dispute, escrow phone numbers are backwards
Root cause: Code swaps phone numbers, saves them to DB permanently
Fix: Don't modify escrow, send B2C directly to client_phone
Impact: Next dispute refund sends to wrong person; data corruption
```

### 🟡 Will Cause Issues

**Missing 'releasing' Status**
```
Symptom: Django validation error when saving status='releasing'
Root cause: Not defined in STATUS_CHOICES
Fix: Add to model (1 line + migration)
Impact: Deliverable approval fails entirely
```

**Refund Conversation ID Not Tracked**
```
Symptom: Refund B2C initiated but callback can't find escrow
Root cause: release_escrow_funds() called but result['conversation_id'] not saved
Fix: Save conversation_id for refunds
Impact: Refund gets stuck in 'refunded' state forever
```

### 🟠 Edge Cases

**No Idempotency Check**
```
Symptom: Client clicks approve twice → funds sent twice
Root cause: No check if already approved
Fix: Check deliverable.status before B2C
Impact: Data loss (overcharging freelancer)
```

**No Callback Timeout**
```
Symptom: Escrow stuck in 'releasing' for hours
Root cause: Callback never fires, no timeout check
Fix: Track b2c_initiated_at, create recovery command
Impact: Stuck funds, no recovery mechanism
```

---

## Test Checklist

**Before production deployment**:

- [ ] `MPESA_B2C_SHORTCODE` is set in `.env`
- [ ] B2C shortcode is **different** from `MPESA_SHORTCODE`
- [ ] Callback URLs are accessible by Safaricom (use ngrok for testing)
- [ ] `releasing` status added to `STATUS_CHOICES`
- [ ] Refund logic updated (no phone swap)
- [ ] Refund conversation_id is tracked
- [ ] Test workflow:
  1. Create project
  2. Freelancer proposes
  3. Client accepts (contract created)
  4. Both sign contract
  5. Client deposits (M-Pesa STK)
  6. Check escrow: status == 'held' ✅
  7. Freelancer submits deliverable
  8. Client approves (B2C initiated)
  9. Check escrow: status == 'releasing' ✅
  10. Wait for callback (~30 secs)
  11. Check escrow: status == 'released' ✅
  12. Freelancer checks wallet: shows in earnings ✅

---

## Debug Commands

```bash
# Check escrow status
python manage.py shell
>>> from core.models import EscrowTransaction
>>> escrow = EscrowTransaction.objects.last()
>>> print(escrow.status, escrow.mpesa_conversation_id, escrow.freelancer_phone)

# Check model issues
python manage.py check

# View M-Pesa callbacks
tail -f mpesa_debug.log

# Test B2C shortcode
python manage.py shell
>>> from core.mpesa_b2c import send_b2c_payment
>>> result = send_b2c_payment('254712345678', 100, 'test', 'test')
>>> print(result)  # Should succeed or show shortcode error
```

---

## Quick Fix Priority

**Do these NOW (2 minutes)**:

1. Add `.env`:
   ```env
   MPESA_B2C_SHORTCODE=600000  # sandbox or your B2C code for prod
   ```

2. Update `models.py` - Add 'releasing' to STATUS_CHOICES (1 line)

3. Update `views.py` - Fix refund phone swap (3 lines)

4. Create migration and migrate

**Then test the whole flow** - should work!

