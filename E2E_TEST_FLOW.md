# End-to-End User Flow – Test Checklist

Use this to test the full flow: **client → project → proposals → accept → contract → M-Pesa deposit → deliverable → approve → M-Pesa release (withdraw)**.

---

## 1. Reset data (already done)

```bash
cd escrow_platform
python manage.py flush_projects --no-input
```

- Deletes all projects, proposals, deliverables, disputes, escrow, contracts.
- **Users are kept** so you can log in as client and freelancer.

---

## 2. Run backend

**Without M-Pesa callbacks (good for everything except deposit/release):**
```bash
cd escrow_platform
python manage.py runserver 0.0.0.0:8000
```

**With M-Pesa (deposit + release to freelancer):**  
Safaricom must reach your app. Use ngrok:

```bash
cd escrow_platform
python start_with_ngrok.py
```

- Starts ngrok on 8000, updates `MPESA_CALLBACK_URL` in `.env`, then runs Django.
- Ensure `.env` has: `NGROK_AUTHTOKEN`, `MPESA_CONSUMER_KEY`, `MPESA_CONSUMER_SECRET`, `MPESA_PASSKEY`, `MPESA_SHORTCODE`.

---

## 3. Run frontend

```bash
cd frontend
npm run dev
```

- App: **http://localhost:5173** (Vite)
- API is proxied to `http://127.0.0.1:8000`.

---

## 4. Test accounts

You need **2 users**:

| Role       | Use for                          |
|-----------|-----------------------------------|
| **Client**   | Create project, accept proposal, deposit, sign contract, approve deliverable |
| **Freelancer** | Find project, send proposal, sign contract, submit deliverable, receive release |

If you don’t have them, register:

1. **Client:** Register → User type: **Client** (email, phone, password).
2. **Freelancer:** Register → User type: **Freelancer** (different email, phone, password).

---

## 5. E2E steps

### A. Client: create project

1. Log in as **client**.
2. Create Project (title, description, scope, timeline, budget).
3. Confirm it appears in **My Projects**.

### B. Freelancer: send proposal

1. Log out, log in as **freelancer**.
2. **Find Work** → open the new project.
3. **Apply** → cover letter, bid amount → Submit.
4. Confirm proposal appears.

### C. Client: accept proposal

1. Log in as **client**.
2. Open the project → **Proposals**.
3. **Accept** the freelancer’s proposal.
4. Project status should move to **Assigned** / **In progress**; escrow record is created.

### D. Both: sign contract

1. **Client:** Project → **Contract** tab → read and **Sign**.
2. **Freelancer:** Project → **Contract** tab → **Sign**.
3. Contract status becomes **Active** when both have signed.

### E. Client: deposit funds (M-Pesa STK)

1. As **client**, open the project.
2. **Deposit** (or similar) → enter **M-Pesa phone** (format e.g. `254712345678`).
3. On your phone: **Enter M-Pesa PIN** when prompted.
4. In **sandbox**, you can use test numbers; in production use a real number.

**For M-Pesa to work:**

- Backend must be reachable by Safaricom → use `start_with_ngrok.py` (and `MPESA_CALLBACK_URL` in `.env`).
- `.env`: `MPESA_CONSUMER_KEY`, `MPESA_CONSUMER_SECRET`, `MPESA_PASSKEY`, `MPESA_SHORTCODE` (and `MPESA_ENVIRONMENT=sandbox` for testing).

### F. Freelancer: submit deliverable

1. Log in as **freelancer**.
2. Open the project → **Deliverables** (or **Deliver**).
3. Upload file + description → **Submit**.
4. Status: **Submitted**.

### G. Client: approve deliverable → release (withdraw to freelancer)

1. Log in as **client**.
2. Open the project → **Deliverables**.
3. **Approve** the deliverable.
4. Backend triggers **M-Pesa B2C** to the freelancer’s phone. After Safaricom confirms, `MpesaReleaseCallbackView` runs and marks escrow as **released**.

### H. Freelancer: check wallet

1. Log in as **freelancer**.
2. **Wallet** (or **My Wallet**): **Total Earnings** and **Transaction History** should show the released amount and status **Released**.

---

## 6. Optional: disputes

- **Raise:** Client or Freelancer → project → **Disputes** → create with reason (and optional evidence).
- **Analyze:** (If implemented) **Analyze** runs AI-style recommendation.
- **Resolve:** (If implemented) **Resolve** with resolution text.

---

## 7. M-Pesa `.env` checklist

For **deposit (STK)** and **release (B2C)** to work:

- `MPESA_ENVIRONMENT=sandbox` (or `production`)
- `MPESA_CONSUMER_KEY`
- `MPESA_CONSUMER_SECRET`
- `MPESA_PASSKEY`
- `MPESA_SHORTCODE`
- `MPESA_CALLBACK_URL` – set by `start_with_ngrok.py` when using ngrok, or your public URL + `/api/mpesa/callback/deposit` and `/api/mpesa/callback/release` as configured in your Django URLs.
- `NGROK_AUTHTOKEN` – only if you use `start_with_ngrok.py`.

---

## 8. If frontend won’t start (`spawn EPERM`)

If `npm run dev` fails with `Error: spawn EPERM` (e.g. from esbuild):

- Run `npm run dev` from a normal **Command Prompt** or **PowerShell** (not necessarily through Cursor).
- Temporarily disable or allow **antivirus/security** for the project folder if it blocks node/esbuild.
- Try: `rm -r node_modules; npm install` (or on Windows: `Remove-Item -Recurse node_modules; npm install`), then `npm run dev` again.
