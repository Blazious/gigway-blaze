#!/usr/bin/env python
"""
Test M-Pesa STK Push (Lipa Na M-Pesa Online) in the backend only.
Run from escrow_platform/ with:  python test_mpesa_stk_backend.py

Prereqs:
  - .env with: MPESA_CONSUMER_KEY, MPESA_CONSUMER_SECRET, MPESA_PASSKEY, MPESA_SHORTCODE
  - MPESA_TEST_MODE=false  (or omit; default is false now)
  - MPESA_CALLBACK_URL=https://YOUR_NGROK_URL/api/mpesa/callback/deposit  (must be HTTPS, reachable by Safaricom)
  - For sandbox: use a number that can receive STK (e.g. test numbers from Safaricom developer portal)
"""
import os
import sys

# Load .env from escrow_platform directory
from pathlib import Path
_script_dir = Path(__file__).resolve().parent
_env = _script_dir / ".env"
if _env.exists():
    from dotenv import load_dotenv
    load_dotenv(_env)
else:
    print("Warning: .env not found in", _script_dir)

# Django setup so we can import from core
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "escrow_platform.settings")
import django
django.setup()

from core.mpesa_config import (
    MPESA_ENVIRONMENT,
    MPESA_TEST_MODE,
    MPESA_CALLBACK_URL,
    MPESA_SHORTCODE,
)
from core.mpesa_auth import get_mpesa_access_token
from core.mpesa_stk import initiate_stk_push


def _mask(s):
    if not s or len(s) < 8:
        return "***"
    return s[:4] + "..." + s[-4:] if len(s) > 8 else "***"


def main():
    print("=" * 60)
    print("M-Pesa STK Push – Backend-only test")
    print("=" * 60)
    print("Config (from .env):")
    print("  MPESA_ENVIRONMENT   =", MPESA_ENVIRONMENT)
    print("  MPESA_TEST_MODE     =", MPESA_TEST_MODE, "(must be False for real STK)")
    print("  MPESA_SHORTCODE     =", MPESA_SHORTCODE)
    print("  MPESA_CALLBACK_URL  =", MPESA_CALLBACK_URL or "(not set)")
    print()

    if MPESA_TEST_MODE:
        print(">>> MPESA_TEST_MODE is True. No real STK will be sent.")
        print("    Set MPESA_TEST_MODE=false in .env to test real M-Pesa.")
        print()
        # Still run auth and “STK” so we see if the rest works
    else:
        if not MPESA_CALLBACK_URL or "yourdomain" in MPESA_CALLBACK_URL:
            print(">>> WARNING: MPESA_CALLBACK_URL must be a real HTTPS URL (e.g. ngrok).")
            print("    Safaricom will POST the result there. Run start_with_ngrok.py or set it in .env.")
            print()

    # 1) Auth
    print("1) Getting M-Pesa access token...")
    try:
        token = get_mpesa_access_token()
        print("   OK. Token:", _mask(token))
    except Exception as e:
        print("   FAILED:", e)
        print("   Check MPESA_CONSUMER_KEY and MPESA_CONSUMER_SECRET in .env.")
        sys.exit(1)

    # 2) STK push
    phone = input("\n2) Enter phone (2547... or 07...): ").strip()
    if not phone:
        phone = "254708374149"  # common sandbox test number
        print("   Using default sandbox test number:", phone)
    try:
        amount = 1  # minimal for sandbox
        ref = "TEST-ESCROW"
        desc = "Backend STK test"
        print("   Initiating STK: amount=KES", amount, "ref=", ref)
        checkout = initiate_stk_push(phone, amount, ref, desc)
        print("   CheckoutRequestID:", checkout)
        if MPESA_TEST_MODE:
            print("   [TEST MODE – no prompt was sent to the phone]")
        else:
            print("   Check your phone for the M-Pesa prompt.")
    except Exception as e:
        print("   STK FAILED:", e)
        sys.exit(1)

    print("\nDone.")


if __name__ == "__main__":
    main()
