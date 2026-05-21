# Escrow Platform Diagnostic - Complete Index

**Status**: 6 Issues Found (2 Critical, 2 High, 2 Medium)  
**Diagnosis Date**: January 26, 2026  
**Est. Fix Time**: 15 minutes (critical), 1 hour (complete)

---

## 📋 Quick Navigation

### For the Impatient (5 minutes)
- Start: [QUICK_REFERENCE.md](QUICK_REFERENCE.md)
- Then: [CODE_FIXES.md](CODE_FIXES.md) - Copy-paste fixes

### For Understanding the System (30 minutes)
1. [COMPLETE_DIAGNOSTIC_SUMMARY.md](COMPLETE_DIAGNOSTIC_SUMMARY.md) - Overview
2. [ARCHITECTURE.md](ARCHITECTURE.md) - How it works
3. [DIAGNOSIS.md](DIAGNOSIS.md) - What's broken

### For Deep Dive (1 hour)
- [BUGS_AND_FIXES.md](BUGS_AND_FIXES.md) - Detailed analysis of each bug
- [CODE_FIXES.md](CODE_FIXES.md) - Exact code changes
- Source files: `core/models.py`, `core/views.py`, `core/mpesa_b2c.py`

---

## 🎯 TL;DR - The 3 Main Problems

### Problem #1: Freelancer Not Getting Paid (B2C Shortcode) 🔴
**What**: B2C payments to freelancers always fail  
**Why**: Using Paybill code (174379) instead of B2C code (600000)  
**Fix**: Add `MPESA_B2C_SHORTCODE=600000` to `.env`  
**Location**: [CODE_FIXES.md#Fix-2](CODE_FIXES.md)

### Problem #2: Dispute Refund Corrupts Data (Phone Swap) 🔴
**What**: After refund, phone numbers are permanently swapped in database  
**Why**: Code swaps phones, saves them to DB  
**Fix**: Remove phone swap, send B2C directly to client phone  
**Location**: [CODE_FIXES.md#Fix-3](CODE_FIXES.md)

### Problem #3: Invalid State in Model (releasing status) 🟡
**What**: Code uses 'releasing' status but model doesn't define it  
**Why**: Incomplete model definition  
**Fix**: Add 'releasing' to STATUS_CHOICES, run migration  
**Location**: [CODE_FIXES.md#Fix-1](CODE_FIXES.md)

---

## 📁 Document Guide

| Document | Best For | Read Time |
|----------|----------|-----------|
| [QUICK_REFERENCE.md](QUICK_REFERENCE.md) | Quick answers to your 4 questions | 5 min |
| [COMPLETE_DIAGNOSTIC_SUMMARY.md](COMPLETE_DIAGNOSTIC_SUMMARY.md) | Full overview of all issues | 10 min |
| [ARCHITECTURE.md](ARCHITECTURE.md) | Understanding the data flow | 15 min |
| [DIAGNOSIS.md](DIAGNOSIS.md) | Detailed issue breakdown | 15 min |
| [BUGS_AND_FIXES.md](BUGS_AND_FIXES.md) | Why each bug exists & how to fix | 20 min |
| [CODE_FIXES.md](CODE_FIXES.md) | Exact code to copy-paste | 10 min |

---

## 🔍 Issue Priority Matrix

| Priority | Issue | Status | Fix Time | Document |
|----------|-------|--------|----------|----------|
| 🔴 CRITICAL | B2C shortcode mismatch | All freelancer withdrawals fail | 2 min | [CODE_FIXES.md](CODE_FIXES.md#fix-2) |
| 🔴 CRITICAL | Dispute refund phone swap | Data corruption | 5 min | [CODE_FIXES.md](CODE_FIXES.md#fix-3) |
| 🟡 HIGH | Missing 'releasing' status | Migration fails or silent error | 5 min | [CODE_FIXES.md](CODE_FIXES.md#fix-1) |
| 🟡 HIGH | Refund conversation ID not tracked | Refund stuck in database | 3 min | [CODE_FIXES.md](CODE_FIXES.md#fix-5) |
| 🟠 MEDIUM | No idempotency checks | Double-approve = double charge | 10 min | [BUGS_AND_FIXES.md](BUGS_AND_FIXES.md#bug-6) |
| 🟠 MEDIUM | No callback timeout | Payment stuck in 'releasing' | 15 min | [BUGS_AND_FIXES.md](BUGS_AND_FIXES.md#bug-5) |

---

## ✅ Answers to Your 4 Questions

### 1. What specific actions are failing after deposit?

**See**: [QUICK_REFERENCE.md#1-what-specific-actions-are-failing](QUICK_REFERENCE.md#1️⃣-what-specific-actions-are-failing-after-deposit)

**Summary**:
- ✅ Deliverable submission works
- ⚠️ Deliverable approval partially works (no guarantees)
- ❌ Freelancer receiving funds likely failing (B2C issue)
- 🔴 Dispute refund corrupts data

---

### 2. What errors are you seeing?

**See**: [QUICK_REFERENCE.md#2-what-errors-are-you-seeing](QUICK_REFERENCE.md#2️⃣-what-errors-are-you-seeing)

**Summary**:
- **Most likely**: Silent failure (B2C shortcode wrong)
- **Possible**: "Invalid shortcode" in M-Pesa response
- **Hidden**: Phone numbers swapped in escrow records
- **Stuck**: Deliverable marked approved but funds not sent

---

### 3. Your current M-Pesa setup?

**See**: [ARCHITECTURE.md#5-m-pesa-configuration](ARCHITECTURE.md#5-m-pesa-configuration)

**Summary**:
- ✅ Using Daraja API (Safaricom) correctly
- ✅ STK Push for deposits works
- ⚠️ B2C API misconfigured (wrong shortcode)
- ✅ Callback infrastructure in place

---

### 4. Show me your escrow transaction model?

**See**: [ARCHITECTURE.md#4-escrow-transaction-model](ARCHITECTURE.md#4-your-escrow-transaction-model)

**Summary**:
- Status field: pending → held → releasing → released → refunded
- Tracks both client & freelancer phones
- Stores M-Pesa receipts and conversation IDs
- One-to-one relationship with Project

---

## 🚀 Quick Start (5 Minutes)

### Step 1: Add to `.env`
```env
MPESA_B2C_SHORTCODE=600000
```

### Step 2: Edit `core/models.py` line 225
Add after `('held', 'Funds Held'),`:
```python
('releasing', 'Releasing'),
```

### Step 3: Edit `core/views.py` lines 794-810
Replace entire `elif decision == 'refund':` block with fixed version from [CODE_FIXES.md](CODE_FIXES.md)

### Step 4: Run migrations
```bash
python manage.py makemigrations core
python manage.py migrate
```

### Step 5: Restart and test
```bash
python start_with_ngrok.py  # Or python manage.py runserver
# Test full E2E flow
```

---

## 📊 Data Flow at a Glance

```
CustomUser
  ├─ Client creates Project
  │   └─ Budget
  │
  └─ Freelancer proposes
      └─ Bid amount
      
      Client accepts
      ├─ Escrow created (pending)
      ├─ Contract created (pending)
      └─ Freelancer assigned
      
      Both sign contract
      ├─ Contract status: signed → active
      └─ Ready for deposit
      
      Client deposits (M-Pesa STK)
      ├─ Safaricom STK Prompt
      ├─ Callback: Escrow held ✅
      └─ Funds locked in escrow
      
      Freelancer submits deliverable
      └─ Deliverable: submitted
      
      Client approves (B2C withdrawal)
      ├─ B2C initiated to freelancer ← BROKEN HERE
      ├─ Escrow: releasing (waiting for callback)
      └─ Callback: Escrow released ✅ (if B2C works)
      
      Freelancer receives funds ✅
      └─ Wallet shows earnings
```

---

## 🐛 Issue Deep Dive

### Issue 1: B2C Shortcode Mismatch 🔴
- **Where**: `core/mpesa_b2c.py` line 57
- **Why**: Using `MPESA_SHORTCODE` (Paybill) instead of B2C code
- **Fix**: See [CODE_FIXES.md#Fix-2](CODE_FIXES.md#fix-2-fix-b2c-shortcode-2-lines)
- **Impact**: ALL freelancer payments fail in production

### Issue 2: Phone Swap Bug 🔴
- **Where**: `core/views.py` lines 794-810
- **Why**: Code swaps phone numbers and saves them to DB
- **Fix**: See [CODE_FIXES.md#Fix-3](CODE_FIXES.md#fix-3-fix-refund-phone-swap-11-lines-removed-restructured)
- **Impact**: Data corruption, wrong recipient on retry

### Issue 3: Missing Status 🟡
- **Where**: `core/models.py` line 225
- **Why**: 'releasing' used but not in STATUS_CHOICES
- **Fix**: See [CODE_FIXES.md#Fix-1](CODE_FIXES.md#fix-1-add-releasing-to-model-1-line--1-migration)
- **Impact**: Migration error or validation failure

### Issue 4: Conversation ID Not Saved 🟡
- **Where**: `core/views.py` lines 800-807
- **Why**: Refund B2C result not tracked
- **Fix**: See [CODE_FIXES.md#Fix-5](CODE_FIXES.md#fix-5-save-conversation-id-for-refunds-add-1-line)
- **Impact**: Refund callback can't find escrow

### Issue 5: No Idempotency 🟠
- **Where**: `core/views.py` lines 480-527
- **Why**: No check if already approved
- **Fix**: See [BUGS_AND_FIXES.md#bug-6](BUGS_AND_FIXES.md#-bug-6-medium---no-idempotency-checks)
- **Impact**: Double-click approval = double payment

### Issue 6: No Timeout Handling 🟠
- **Where**: Multiple files
- **Why**: No recovery for stuck 'releasing' state
- **Fix**: See [BUGS_AND_FIXES.md#bug-5](BUGS_AND_FIXES.md#-bug-5-medium---no-callback-timeout-handling)
- **Impact**: Stuck payments with no recovery

---

## 🧪 Test Scenarios

### Scenario 1: Deposit Works ✅
```
1. Client has phone: 254712345678
2. POST /api/escrow/deposit/ with this phone
3. M-Pesa prompt appears on phone
4. Enter PIN
5. Callback fires → Escrow status: held ✅
```

### Scenario 2: Approval Initiates B2C (currently broken) ❌
```
1. Freelancer phone: 254712345999
2. Client POST /api/deliverables/{id}/approve/
3. B2C initiated with WRONG shortcode
4. Safaricom returns error (not visible to user)
5. Escrow stuck in 'releasing' state ❌
```

### Scenario 3: Refund Corrupts Data (currently broken) 🔴
```
1. Dispute raised
2. Admin POST /api/disputes/{id}/resolve/ with decision=refund
3. Phones SWAPPED in escrow object
4. B2C sends to client (works by accident)
5. Phones saved SWAPPED to database
6. Next refund sends to FREELANCER instead of client ❌
```

---

## 📞 Troubleshooting

### "Funds showing as 'releasing' forever"
- Check if B2C shortcode is correct: [CODE_FIXES.md#Fix-2](CODE_FIXES.md#fix-2-fix-b2c-shortcode-2-lines)
- Check if callback URL is reachable: Use ngrok (`python start_with_ngrok.py`)
- Check logs: `tail -f mpesa_debug.log`

### "Phone numbers swapped in database"
- Don't use refund endpoint until fixed: [CODE_FIXES.md#Fix-3](CODE_FIXES.md#fix-3-fix-refund-phone-swap-11-lines-removed-restructured)
- Can manually fix in DB or revert data

### "Migration error about 'releasing'"
- Add status to model: [CODE_FIXES.md#Fix-1](CODE_FIXES.md#fix-1-add-releasing-to-model-1-line--1-migration)
- Run migrations: `python manage.py migrate`

---

## 📚 Related Files

**Models**:
- `core/models.py` - EscrowTransaction (lines 218-267)
- `core/models.py` - Contract (lines 269-297)
- `core/models.py` - Project (lines 84-122)

**Views**:
- `core/views.py` - EscrowDepositView (lines 355-428)
- `core/views.py` - DeliverableApproveView (lines 480-527)
- `core/views.py` - DisputeResolveView (lines 740-820)
- `core/views.py` - MpesaReleaseCallbackView (lines 457-475)

**M-Pesa**:
- `core/mpesa_b2c.py` - send_b2c_payment (lines 50-112)
- `core/mpesa_b2c.py` - release_escrow_funds (lines 29-45)
- `core/mpesa_callbacks.py` - process_b2c_callback (lines 67-113)
- `core/mpesa_stk.py` - initiate_stk_push (full file)

**Configuration**:
- `.env` - Environment variables (needs MPESA_B2C_SHORTCODE)
- `core/mpesa_config.py` - M-Pesa settings

---

## ✨ After Fixes (Expected Behavior)

```
1. Client deposits: Escrow → held ✅
2. Freelancer submits: Deliverable → submitted ✅
3. Client approves: B2C initiated ✅
4. Callback arrives: Escrow → released ✅
5. Freelancer checks wallet: Shows earned amount ✅
6. Dispute refund: Funds go to client (phone unmodified) ✅
7. Retry operations: Idempotent (safe to retry) ✅
8. Stuck payment: Detectable via timeout field ✅
```

---

## 🎓 Learning Resources Included

- **ARCHITECTURE.md**: Learn how the system works
- **BUGS_AND_FIXES.md**: Understand why bugs exist
- **CODE_FIXES.md**: See exact code changes
- **QUICK_REFERENCE.md**: Quick lookup guide

---

## 📝 Next Actions Checklist

- [ ] Read QUICK_REFERENCE.md (5 min)
- [ ] Read CODE_FIXES.md (10 min)
- [ ] Add MPESA_B2C_SHORTCODE to .env (1 min)
- [ ] Edit models.py (1 min)
- [ ] Edit views.py (5 min)
- [ ] Run migrations (1 min)
- [ ] Test full E2E flow (15 min)
- [ ] Deploy to production (5 min)

**Total**: ~45 minutes to full deployment

---

## 📞 Support

All information needed to understand and fix these issues is in the documents above.

For each issue:
1. Check the priority table above
2. Find the issue in appropriate document
3. Follow the fix in CODE_FIXES.md
4. Test per test scenarios above

---

**Good luck with the fixes! The architecture is solid once these bugs are addressed. 🚀**

