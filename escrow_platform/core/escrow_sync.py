import json
import logging

from django.utils import timezone

from core.intasend_gateway import get_transaction_status
from core.models import Contract, Escrow
from core.notification_service import send_payment_notification

logger = logging.getLogger(__name__)


def extract_econfirm_payload(response_data):
    """eConfirm may wrap transaction details under `data`."""
    if isinstance(response_data, dict) and isinstance(response_data.get('data'), dict):
        return response_data.get('data')
    return response_data if isinstance(response_data, dict) else {}


def _state_from_payload(payload):
    raw_state = (
        payload.get('status')
        or payload.get('state')
        or payload.get('payment_status')
        or payload.get('escrow_status')
        or ''
    )
    return str(raw_state).lower()


def _update_from_payload(escrow, payload, *, notify=False):
    confirmation_code = (
        payload.get('confirmation_code')
        or payload.get('mpesa_confirmation_code')
        or payload.get('mpesa_receipt')
        or payload.get('receipt')
        or payload.get('provider_reference')
        or payload.get('payment_reference')
    )
    state = _state_from_payload(payload)

    deposit_reference = (
        payload.get('provider_reference')
        or payload.get('payment_reference')
        or payload.get('receipt')
        or 'ECONFIRM-SYNC'
    )
    release_reference = (
        payload.get('release_reference')
        or payload.get('provider_reference')
        or payload.get('receipt')
        or 'ECONFIRM-RELEASE'
    )

    contract = escrow.contract
    project = contract.project

    is_funded_state = any(token in state for token in ['funded', 'held', 'complete', 'completed', 'paid', 'success'])
    is_released_state = any(token in state for token in ['released', 'settled'])
    is_failed_state = any(token in state for token in ['failed', 'cancelled', 'canceled', 'expired'])

    if is_funded_state and escrow.status in ['pending', 'failed']:
        escrow.status = 'held'
        escrow.mpesa_receipt = deposit_reference
        if confirmation_code:
            escrow.confirmation_code = confirmation_code
        escrow.save()

        contract.payment_status = 'escrowed'
        contract.save()

        if project.status in ['assigned', 'open']:
            project.status = 'in_progress'
            project.save()

        if notify:
            send_payment_notification(escrow, 'payment_deposited', contract.client)

    if is_released_state and escrow.status == 'releasing':
        escrow.status = 'released'
        escrow.mpesa_release_receipt = release_reference
        escrow.released_at = timezone.now()
        escrow.save()

        contract.payment_status = 'released'
        contract.status = 'completed'
        contract.completed_at = timezone.now()
        contract.save()

        if project.status != 'completed':
            project.status = 'completed'
            project.save()

        if notify:
            send_payment_notification(escrow, 'payment_released', contract.freelancer)

    if is_failed_state and escrow.status == 'pending':
        escrow.status = 'failed'
        escrow.save()

    return escrow


def sync_escrow_from_provider(escrow):
    """
    Sync local escrow status from eConfirm transaction state.
    Returns updated escrow instance.
    """
    if not getattr(escrow, 'mpesa_checkout_request_id', None):
        return escrow

    response_data = get_transaction_status(escrow.mpesa_checkout_request_id)
    payload = extract_econfirm_payload(response_data)
    return _update_from_payload(escrow, payload)


def process_econfirm_webhook(body):
    """Best-effort eConfirm webhook handler for transaction status callbacks."""
    try:
        if isinstance(body, bytes):
            callback = json.loads(body.decode('utf-8'))
        elif isinstance(body, str):
            callback = json.loads(body)
        else:
            callback = body if isinstance(body, dict) else {}

        payload = extract_econfirm_payload(callback)
        transaction_id = (
            payload.get('transaction_id')
            or payload.get('id')
            or payload.get('escrow_id')
            or callback.get('transaction_id')
            or callback.get('id')
        )
        if not transaction_id:
            return False, 'No eConfirm transaction id in webhook'

        escrow = Escrow.objects.get(mpesa_checkout_request_id=transaction_id)
        _update_from_payload(escrow, payload, notify=True)
        return True, 'eConfirm webhook processed'
    except Escrow.DoesNotExist:
        return False, 'Escrow record not found'
    except Exception as exc:
        logger.exception("Error processing eConfirm webhook")
        return False, str(exc)
