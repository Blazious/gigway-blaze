# Escrow Testing Guide

This guide explains how to test the M-Pesa escrow feature directly from the backend without using the frontend.

## Prerequisites

1. Django server should be running (or you can run tests directly)
2. M-Pesa credentials configured in `.env` file
3. Ngrok running (if testing real callbacks) OR use simulated callbacks

## Test Scripts

### 1. Simple Deposit Test (Recommended)

**File**: `test_deposit_simple.py`

This is the easiest way to test just the deposit flow.

#### Usage:

```bash
# Test deposit flow
python test_deposit_simple.py <client_phone> <freelancer_phone> [amount]

# Example:
python test_deposit_simple.py 254712345678 254798765432 10
```

This will:
1. Create test client and freelancer users
2. Create a project
3. Create and sign a contract
4. Create an escrow transaction
5. Initiate M-Pesa STK Push

After running, **check your phone** for the M-Pesa prompt and complete the payment.

#### Simulate Callback:

After completing payment (or to test without real payment), simulate the callback:

```bash
python test_deposit_simple.py --simulate-callback <checkout_id>
```

The checkout ID will be printed when you run the deposit test.

---

### 2. Full Workflow Test

**File**: `test_full_escrow_workflow.py`

Tests the complete escrow workflow including deposit, release, and refund flows.

#### Usage:

```bash
python test_full_escrow_workflow.py
```

This is an interactive script that will:
1. Ask for phone numbers
2. Create all necessary users, projects, contracts
3. Test deposit flow
4. Optionally test release flow (B2C payment to freelancer)
5. Optionally test refund flow

---

### 3. Quick Deposit Test (Interactive)

**File**: `test_deposit_only.py`

Interactive version for quick testing.

```bash
python test_deposit_only.py
```

---

## Testing Workflow

### Step 1: Test Deposit

```bash
cd escrow_platform
python test_deposit_simple.py 254712345678 254798765432 10
```

**Output:**
```
============================================================
DEPOSIT TEST
============================================================

Client: test_client_20241201120000@test.com (254712345678)
Freelancer: test_freelancer_20241201120000@test.com (254798765432)
Amount: KES 10.0

✓ Client created: test_client_20241201120000@test.com
✓ Freelancer created: test_freelancer_20241201120000@test.com
✓ Project created: <project_id>
✓ Contract signed
✓ Escrow created: <escrow_id>

============================================================
INITIATING M-PESA STK PUSH...
============================================================

✓ STK Push initiated!
  Checkout Request ID: abc123xyz...

============================================================
ACTION REQUIRED:
1. Check your phone for M-Pesa prompt
2. Enter your M-Pesa PIN
3. Complete the payment
============================================================

Checkout ID: abc123xyz...
```

### Step 2: Complete Payment

Check your phone and complete the M-Pesa payment.

### Step 3: Simulate Callback (or wait for real callback)

If using ngrok and real M-Pesa, the callback will come automatically.

To simulate (for testing):

```bash
python test_deposit_simple.py --simulate-callback abc123xyz
```

**Expected Output:**
```
✓ Callback processed: Deposit processed successfully

Escrow Status: held
Receipt: TEST20241201120000
Project Status: in_progress
Deposited At: 2024-12-01 12:00:00
```

### Step 4: Verify in Django Admin

1. Go to Django admin: `http://localhost:8000/admin/`
2. Check `EscrowTransaction` - status should be `held`
3. Check `Project` - status should be `in_progress`

---

## Troubleshooting

### Issue: "M-Pesa credentials not configured"

**Solution**: Make sure your `.env` file has:
```env
MPESA_CONSUMER_KEY=your_key
MPESA_CONSUMER_SECRET=your_secret
MPESA_SHORTCODE=174379
MPESA_PASSKEY=your_passkey
MPESA_CALLBACK_URL=https://your-ngrok-url.ngrok-free.app/api/mpesa/callback/deposit
```

### Issue: "STK Push failed"

**Possible causes:**
1. Invalid phone number format (should be 2547...)
2. M-Pesa credentials incorrect
3. Network issues
4. Sandbox account issues

**Check:**
- Phone number format: `254712345678` (Kenya format)
- M-Pesa sandbox credentials are correct
- Network connectivity

### Issue: "EscrowTransaction not found for checkout"

**Solution**: Make sure you're using the correct checkout ID from the deposit test output.

### Issue: Callback not received

**If using real M-Pesa:**
1. Check ngrok is running: `ngrok http 8000`
2. Verify callback URL in `.env` matches ngrok URL
3. Check Django server logs for callback attempts
4. M-Pesa callbacks may take a few seconds

**If simulating:**
- Use the `--simulate-callback` flag with the checkout ID

---

## Testing Release Flow

After deposit is successful (status = `held`), you can test releasing funds:

### Using Django Shell:

```python
python manage.py shell

from core.models import EscrowTransaction, Deliverable, Project
from core.mpesa_b2c import send_b2c_payment
from django.utils import timezone

# Get escrow
escrow = EscrowTransaction.objects.get(status='held')

# Create deliverable
deliverable = Deliverable.objects.create(
    project=escrow.project,
    freelancer=escrow.project.freelancer,
    file_url="test.pdf",
    description="Test deliverable",
    status='submitted'
)

# Send B2C payment
result = send_b2c_payment(
    phone_number=escrow.freelancer_phone,
    amount=float(escrow.amount),
    occasion=f"Payment for {escrow.project.title}",
    remarks="Freelancer payment via escrow"
)

# Update escrow
escrow.mpesa_conversation_id = result['conversation_id']
escrow.status = 'releasing'
escrow.release_initiated_at = timezone.now()
escrow.save()

print(f"B2C payment sent! Conversation ID: {result['conversation_id']}")
```

---

## Quick Test Checklist

- [ ] M-Pesa credentials configured in `.env`
- [ ] Django server running (or test scripts work standalone)
- [ ] Phone numbers ready (client and freelancer)
- [ ] Run deposit test
- [ ] Complete M-Pesa payment on phone
- [ ] Simulate callback OR wait for real callback
- [ ] Verify escrow status is `held`
- [ ] Verify project status is `in_progress`

---

## Notes

- All test scripts create temporary users/projects - safe to run multiple times
- Phone numbers are automatically formatted to Kenya format (2547...)
- Test scripts use small amounts (default 10 KES) - safe for testing
- Real M-Pesa requires ngrok for callbacks in development
- Simulated callbacks work without ngrok for testing
