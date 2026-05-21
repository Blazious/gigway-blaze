# GigWay Escrow Platform

A secure escrow platform for freelancers and clients with M-Pesa integration.

## Features

- **Project Management**: Create, track, and manage projects
- **Escrow Payments**: Secure funds until work is completed
- **M-Pesa Integration**: Mobile money payments via STK Push
- **Dispute Resolution**: AI-assisted mediation system
- **Delivery Tracking**: Submit and approve deliverables

## Run Fullstack Locally

On Windows, start both Django and Vite with:

```bat
start-dev.cmd
```

This opens two server windows:
- Backend: `http://127.0.0.1:8000/`
- Frontend: `http://127.0.0.1:5173/`
- Backend health check: `http://127.0.0.1:8000/api/health/`

Close the two server windows to stop the app, or run:

```bat
stop-dev.cmd
```

The launcher uses `npm.cmd`, so it avoids the common PowerShell `npm.ps1` execution-policy error.

## Manual Setup

1. Install frontend dependencies:
```bash
cd frontend
npm install
```

2. Start Django:
```bash
cd escrow_platform
python manage.py runserver 127.0.0.1:8000 --noreload
```

3. Start Vite in another terminal:
```bash
cd frontend
npm run dev
```

## Demo Accounts

#### Client Account
- Email: client@demo.com
- Password: demo123

#### Freelancer Account
- Email: freelancer@demo.com
- Password: demo123

#### Admin Account
- Email: admin@demo.com
- Password: demo123

## Test M-Pesa Numbers
Use these test numbers (safaricom sandbox):
- 254708374149 (success)
- 254708374143 (fail)

## Demo Flow

### Client Workflow
1. Create a project
2. Assign to freelancer
3. Deposit funds to escrow via M-Pesa
4. Approve/review deliverables
5. Raise disputes if needed

### Freelancer Workflow
1. Browse available projects
2. Apply for projects
3. Sign contract
4. Submit deliverables
5. Track payments

### Admin Workflow
1. Monitor all projects
2. Review disputes
3. Analyze with AI
4. Enforce resolutions

## Screenshots
📸 See screenshots in the `/demo-screenshots` folder.

## Technologies Used
- React.js
- Tailwind CSS
- Node.js (Backend)
- M-Pesa API (STK Push)
- OpenAI (Dispute Analysis)
