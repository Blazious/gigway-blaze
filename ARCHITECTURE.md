# Your Escrow Architecture - Detailed Breakdown

## Project Structure Overview

```
CustomUser (email, phone_number, user_type: client|freelancer)
    │
    ├── Client creates Project (title, description, budget, timeline)
    │
    └── Freelancer finds Project → Proposes (cover_letter, bid_amount)
        
        Client accepts Proposal
        ├── Project.freelancer assigned
        ├── Project.status = 'assigned'
        ├── Contract created (status: 'pending')
        └── EscrowTransaction created (status: 'pending')
            
            Both sign Contract (Client + Freelancer signatures)
            └── Contract.status = 'active'
            
            Client deposits funds via M-Pesa
            └── EscrowTransaction.status = 'held'
                ├── mpesa_checkout_request_id set
                ├── mpesa_deposit_receipt stored
                └── deposited_at recorded
                
            Freelancer submits Deliverable
            └── Deliverable.status = 'submitted'
            
            Client approves Deliverable
            ├── Deliverable.status = 'approved'
            ├── B2C payment initiated to freelancer
            ├── EscrowTransaction.status = 'releasing'
            └── Project.status = 'completed'
                
                M-Pesa B2C callback fires
                └── EscrowTransaction.status = 'released'
                    ├── mpesa_conversation_id matched
                    ├── mpesa_release_receipt stored
                    └── released_at recorded
```

---

## 1. DEPOSIT FLOW (Client → Safaricom → Freelancer funds)

### Step 1: Client calls EscrowDepositView
**Endpoint**: `POST /api/escrow/deposit/`

**Request**:
```json
{
  "project_id": "uuid-of-project",
  "phone_number": "254712345678"  // Client's M-Pesa phone
}
```

**Validation**:
- ✅ User is a client
- ✅ Contract exists
- ✅ Both signatures present (client_signature AND freelancer_signature)

**Action**:
```python
# Get or create EscrowTransaction
escrow = EscrowTransaction.objects.get_or_create(
    project=project,
    defaults={
        'client_phone': '254712345678',      # From request
        'freelancer_phone': 'project.freelancer.phone_number',
        'amount': project.budget,
        'status': 'pending'
    }
)

# Initiate STK Push
checkout_id = initiate_stk_push(
    phone_number='254712345678',
    amount=project.budget,
    account_reference=f'ESCROW-{project.id}',
    transaction_desc=f'Payment for {project.title}'
)

# Save checkout ID
escrow.mpesa_checkout_request_id = checkout_id
escrow.save()
```

**Response**:
```json
{
  "status": "pending",
  "message": "Check your phone for M-Pesa payment prompt",
  "checkout_request_id": "...",
  "escrow": {...}
}
```

---

### Step 2: M-Pesa Prompt on Phone
- User receives USSD prompt
- Enters PIN
- Safaricom processes payment
- Safaricom calls your webhook

---

### Step 3: Safaricom Callback (MpesaCallbackView)
**Webhook URL** (set in `.env`): `https://your-ngrok-url/api/mpesa/callback/deposit/`

**Incoming Callback** (from Safaricom):
```json
{
  "Body": {
    "stkCallback": {
      "CheckoutRequestID": "...",  // Matches escrow.mpesa_checkout_request_id
      "ResultCode": 0,              // 0 = success
      "ResultDesc": "The service request has been processed successfully.",
      "CallbackMetadata": {
        "Item": [
          {"Name": "Amount", "Value": "100"},
          {"Name": "MpesaReceiptNumber", "Value": "LGH61AF60SG"},  // Important!
          {"Name": "PhoneNumber", "Value": "254712345678"}
        ]
      }
    }
  }
}
```

**Processing** (`process_deposit_callback`):
```python
1. Extract CheckoutRequestID
2. Find EscrowTransaction by mpesa_checkout_request_id
3. If ResultCode == 0:
   ├── Extract MpesaReceiptNumber
   ├── escrow.status = 'held'
   ├── escrow.mpesa_deposit_receipt = receipt_number
   ├── escrow.deposited_at = now()
   ├── escrow.save()
   ├── project.status = 'in_progress'
   ├── project.contract.status = 'active'  ✅ Funds locked
4. Else:
   └── escrow.status = 'failed'
```

**Result**: 
- ✅ Funds are now in Safaricom escrow account
- ✅ Neither client nor freelancer can access them
- ✅ Awaiting deliverable and approval

---

## 2. APPROVAL FLOW (Deliverable → B2C Release)

### Step 1: Client approves Deliverable
**Endpoint**: `POST /api/deliverables/{deliverable_id}/approve/`

**Validation**:
- ✅ User is project owner (client)
- ✅ Escrow exists and status == 'held'

**Action**:
```python
deliverable.status = 'approved'
deliverable.save()

escrow = deliverable.project.escrow

# INITIATE B2C PAYMENT
payment_result = send_b2c_payment(
    phone_number=escrow.freelancer_phone,        # 254712345999
    amount=float(escrow.amount),
    occasion=f"Payment for {project.title}",
    remarks="Freelancer payment via escrow"
)

# Save conversation ID
escrow.mpesa_conversation_id = payment_result['conversation_id']
escrow.status = 'releasing'  # ⚠️ Not in STATUS_CHOICES!
escrow.save()

project.status = 'completed'
project.save()
```

**Response**:
```json
{
  "message": "Deliverable approved. Funds being released to freelancer.",
  "conversation_id": "..."
}
```

---

### Step 2: B2C Payment Request to Safaricom
**mpesa_b2c.py - send_b2c_payment()**:

```python
def send_b2c_payment(phone_number, amount, occasion, remarks):
    phone = format_phone_number(phone_number)  # → '254712345999'
    
    # ⚠️ CRITICAL: B2C shortcode selection
    if settings.MPESA_ENVIRONMENT == 'sandbox':
        b2c_shortcode = '600000'  # Sandbox shortcode ✅
    else:
        b2c_shortcode = settings.MPESA_SHORTCODE  # ⚠️ Might be Paybill (174379)!
    
    payload = {
        "InitiatorName": "testapi",
        "SecurityCredential": "<base64-encoded-password>",
        "CommandID": "BusinessPayment",
        "Amount": "100",                         # integer
        "PartyA": b2c_shortcode,                # Safaricom holds funds here
        "PartyB": "254712345999",               # Freelancer's phone
        "Remarks": "Freelancer payment via escrow",
        "QueueTimeOutURL": "https://your-url/api/mpesa/callback/release/",
        "ResultURL": "https://your-url/api/mpesa/callback/release/",
        "Occasion": "Payment for Project X"
    }
    
    # POST to Safaricom
    response = requests.post(
        MPESA_BASE_URL + "/mpesa/b2c/v1/paymentrequest",
        headers={
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        },
        data=json.dumps(payload)
    )
    
    # Response:
    {
        "ConversationID": "AG_...",           # Save this!
        "OriginatorConversationID": "..."
    }
```

**Possible Errors**:
- ❌ `ResultCode: 500` - Invalid shortcode (Paybill instead of B2C)
- ❌ `ResultCode: 400` - Invalid phone format
- ❌ `ResultCode: 1001` - Insufficient funds
- ❌ Connection timeout - Callback URL unreachable

---

### Step 3: Safaricom B2C Callback
**Webhook URL**: `https://your-url/api/mpesa/callback/release/`

**Incoming Callback** (sync or async):
```json
{
  "Result": {
    "ResultType": 0,
    "ResultCode": 0,
    "ResultDesc": "The service request has been processed successfully.",
    "ConversationID": "AG_...",           // Must match what we saved
    "OriginatorConversationID": "...",
    "InitiatedTime": "2024-01-26 14:30:00",
    "TransactionID": "LGH61AF60SG",
    "ResultParameters": {
      "ResultParameter": [
        {"Key": "TransactionReceipt", "Value": "LGH61AF60SG"},
        {"Key": "TransactionAmount", "Value": "100"},
        {"Key": "B2CUtilityAccountAvailable", "Value": "1"},
        {"Key": "B2CWorkingAccountAvailable", "Value": "1"},
        {"Key": "TransactionCompletedDateTime", "Value": "26.01.2024 14:30:00"}
      ]
    }
  }
}
```

**Processing** (`process_b2c_callback`):
```python
1. Extract ConversationID
2. Find EscrowTransaction by mpesa_conversation_id
3. If ResultCode == 0:
   ├── Extract TransactionReceipt
   ├── escrow.status = 'released'  ✅
   ├── escrow.mpesa_release_receipt = receipt
   ├── escrow.released_at = now()
   ├── escrow.save()
   └── Freelancer now has funds! ✅
4. Else:
   └── escrow.status = 'failed'
        └── Funds stay in escrow (could retry)
```

---

## 3. WALLET VIEW (Freelancer checks earnings)

**Endpoint**: `GET /api/wallet/`

**For Freelancer**:
```python
projects = Project.objects.filter(freelancer=request.user)

for project in projects:
    if hasattr(project, 'escrow'):
        escrow = project.escrow
        
        if escrow.status == 'held':
            in_escrow += escrow.amount
        elif escrow.status == 'released':
            total_earnings += escrow.amount
```

**Response**:
```json
{
  "in_escrow": 500.00,         // Awaiting deliverable approval
  "total_earnings": 2500.00,    // Already received
  "transactions": [
    {
      "id": "uuid",
      "project_title": "Build Mobile App",
      "amount": "500.00",
      "status": "released",      // or "held"
      "date": "2024-01-26",
      "receipt": "LGH61AF60SG"
    }
  ]
}
```

---

## 4. DISPUTE FLOW (⚠️ BUG HERE)

### Step 1: Raise Dispute
**Endpoint**: `POST /api/disputes/`

Either party can raise if there's a disagreement.

```python
dispute = Dispute.objects.create(
    project=project,
    raised_by=request.user,  # Client or Freelancer
    reason="Deliverable not as specified",
    evidence_url="path/to/file",
    status='open'
)
project.status = 'disputed'
```

---

### Step 2: Resolve Dispute
**Endpoint**: `POST /api/disputes/{dispute_id}/resolve/`

Admin/arbiter calls this with decision.

**Request**:
```json
{
  "decision": "release",        // or "refund"
  "percentage": 100,            // % of escrow to release (if release)
  "resolution_notes": "Freelancer completed work satisfactorily"
}
```

---

### Step 3: Release Decision 🔴 BUG
```python
if decision == 'release':
    result = release_escrow_funds(escrow, percentage)  # ✅ Works
    escrow.status = 'releasing'
    escrow.save()
```

---

### Step 4: Refund Decision 🔴 BUG (PHONE SWAP)
```python
if decision == 'refund':
    # ❌ BUGGY CODE - Swaps phone numbers permanently!
    client_phone = escrow.client_phone
    escrow.client_phone = escrow.freelancer_phone
    escrow.freelancer_phone = client_phone
    
    # Now freelancer_phone points to CLIENT
    # B2C sends funds to client
    result = release_escrow_funds(escrow, 100)
    
    # ❌ Problem: These modified phone numbers are saved!
    escrow.status = 'refunded'
    escrow.save()
```

**What happens next time**:
- Someone checks the escrow → phone numbers are swapped
- If dispute is resolved again → funds go to WRONG person!
- Data corruption

**Correct approach**:
```python
if decision == 'refund':
    # ✅ Don't modify escrow, use separate vars for B2C
    result = release_escrow_funds_to_client(
        phone_number=escrow.client_phone,  # Explicitly send to client
        amount=escrow.amount
    )
    
    # Update escrow WITHOUT modifying phone numbers
    escrow.status = 'refunded'
    escrow.save()
```

---

## 5. M-PESA CONFIGURATION

### .env Required Variables:
```env
MPESA_ENVIRONMENT=sandbox              # or production
MPESA_CONSUMER_KEY=...
MPESA_CONSUMER_SECRET=...
MPESA_PASSKEY=...                      # For STK
MPESA_SHORTCODE=174379                 # Paybill (for STK deposits) ✅
MPESA_B2C_SHORTCODE=600000             # B2C shortcode (for releases) ✅
MPESA_CALLBACK_BASE_URL=https://your-ngrok.ngrok-free.app
NGROK_AUTHTOKEN=...                    # For start_with_ngrok.py
```

### Important URLs:
- Deposit callback: `{MPESA_CALLBACK_BASE_URL}/api/mpesa/callback/deposit/`
- Release callback: `{MPESA_CALLBACK_BASE_URL}/api/mpesa/callback/release/`

Both must be reachable and match what you register with Safaricom.

---

## 6. STATE TRANSITIONS (Current)

```
                     ┌─────────────────┐
                     │    PENDING      │  (Escrow created)
                     └────────┬────────┘
                              │ M-Pesa deposit succeeds
                              ▼
                     ┌─────────────────┐
                     │      HELD       │  (Funds locked in escrow)
                     └────────┬────────┘
                   ┌──────────┴──────────┐
                   │                     │
         Deliverable approved   Dispute → Refund
                   │                     │
                   ▼                     ▼
          ┌──────────────────┐   ┌──────────────┐
          │   RELEASING      │   │  REFUNDED    │
          └────────┬─────────┘   └──────────────┘
                   │ B2C callback succeeds
                   ▼
          ┌──────────────────┐
          │   RELEASED       │  (Funds to freelancer) ✅
          └──────────────────┘
```

**Problems**:
- `RELEASING` state not in `STATUS_CHOICES` ❌
- No `FAILED` state for callback failures
- No idempotency checks (same approve called twice?)
- No timeout handling for stuck `RELEASING` state

---

## 7. KEY RELATIONSHIPS

```python
# One-to-One Relationships:
EscrowTransaction.project → Project
Contract.project → Project

# One-to-Many Relationships:
Project.deliverables → Deliverable[]
Project.disputes → Dispute[]
Project.proposals → Proposal[]  (historical)

# Key Foreign Keys:
Project.client → CustomUser
Project.freelancer → CustomUser
Deliverable.freelancer → CustomUser
Dispute.raised_by → CustomUser
```

**Query Example**:
```python
# Get all freelancer earnings
freelancer = CustomUser.objects.get(email='freelancer@example.com')
released_projects = Project.objects.filter(
    freelancer=freelancer,
    escrow__status='released'
)
total_earned = released_projects.aggregate(
    Sum('escrow__amount')
)['escrow__amount__sum']
```

