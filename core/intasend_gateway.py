import logging
import os
from typing import Any, Dict, Optional

import requests

logger = logging.getLogger(__name__)

DEFAULT_TIMEOUT_SECONDS = 30


def _normalize_phone_number(phone_number: str) -> str:
    phone = str(phone_number).strip().replace("+", "").replace(" ", "")
    if phone.startswith("0"):
        phone = f"254{phone[1:]}"
    elif not phone.startswith("254"):
        phone = f"254{phone}"
    return phone


def _get_v1_base_url() -> str:
    return os.getenv("ECONFIRM_V1_BASE_URL", "https://econfirm.co.ke/api/v1").rstrip("/")


def _get_api_key() -> str:
    api_key = os.getenv("ECONFIRM_API_KEY", "").strip()
    if not api_key:
        raise ValueError("ECONFIRM_API_KEY is not configured")
    return api_key


def _request(
    method: str,
    path: str,
    payload: Optional[Dict[str, Any]] = None,
    timeout: int = DEFAULT_TIMEOUT_SECONDS,
) -> Dict[str, Any]:
    headers = {
        "Authorization": f"Bearer {_get_api_key()}",
        "Accept": "application/json",
    }
    if payload is not None:
        headers["Content-Type"] = "application/json"

    url = f"{_get_v1_base_url()}{path}"
    response = requests.request(
        method=method,
        url=url,
        headers=headers,
        json=payload,
        timeout=timeout,
    )
    try:
        body = response.json()
    except ValueError:
        body = {"raw": response.text}

    if response.status_code >= 400:
        logger.error("eConfirm API error %s on %s: %s", response.status_code, url, body)
        raise Exception(f"eConfirm API error ({response.status_code}): {body}")

    return body


def get_intasend_service():
    """
    Backward-compatible alias used by existing views/tests.
    Returns metadata so imports continue to work.
    """
    return {"provider": "econfirm", "base_url": _get_v1_base_url()}


def initiate_escrow_deposit(
    phone_number,
    amount,
    account_reference,
    buyer_email=None,
    seller_email=None,
    receiver_phone=None,
    description=None,
    terms=None,
):
    """
    Creates an escrow transaction then triggers STK Push funding.
    Returns the eConfirm transaction ID.
    """
    try:
        phone = _normalize_phone_number(phone_number)
        transaction_payload = {
            "buyer_email": buyer_email or "buyer@example.com",
            "seller_email": seller_email or "seller@example.com",
            "amount": float(amount),
            "currency": "KES",
            "description": description or f"Escrow funding for {account_reference}",
            "terms": terms or "Release after client approval.",
        }
        if receiver_phone:
            transaction_payload["receiver_phone"] = _normalize_phone_number(receiver_phone)
        transaction = _request("POST", "/transactions", transaction_payload)
        transaction_id = (
            transaction.get("id")
            or transaction.get("transaction_id")
            or transaction.get("data", {}).get("id")
        )
        if not transaction_id:
            raise Exception(f"Missing transaction id from eConfirm response: {transaction}")

        stk_payload = {
            "transaction_id": transaction_id,
            "payer_phone": phone,
        }
        stk_response = _request("POST", "/payments/stk-push", stk_payload)
        logger.info("eConfirm STK Push initiated for transaction %s", transaction_id)
        logger.debug("eConfirm STK response: %s", stk_response)
        return transaction_id
    except Exception as e:
        logger.exception("Failed to initiate eConfirm deposit")
        raise Exception(f"Payment gateway error: {str(e)}")


def release_escrow_funds(transaction_id, confirmation_code, notes="Client approved delivery"):
    """
    Releases held escrow funds to seller.
    Returns transaction ID as release tracking key.
    """
    try:
        payload = {
            "confirmation_code": confirmation_code,
            "notes": notes,
        }
        _request("POST", f"/transactions/{transaction_id}/release", payload)
        logger.info("eConfirm release initiated for transaction %s", transaction_id)
        return transaction_id
    except Exception as e:
        logger.exception("Failed to initiate eConfirm release")
        raise Exception(f"Payout gateway error: {str(e)}")


def get_transaction_status(transaction_id):
    """Fetch transaction details/status from eConfirm."""
    try:
        return _request("GET", f"/transactions/{transaction_id}", timeout=8)
    except Exception as e:
        logger.exception("Failed to fetch eConfirm transaction status")
        raise Exception(f"Status lookup error: {str(e)}")
