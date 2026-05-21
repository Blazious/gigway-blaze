import json
import logging
from datetime import datetime
from django.utils import timezone
from core.models import Escrow, Contract
from core.notification_service import send_payment_notification

logger = logging.getLogger(__name__)

def process_intasend_webhook(body_str):
    """
    Process IntaSend webhooks for Collections (STK Push) and Payouts.
    Returns: tuple (success: bool, message: str)
    """
    try:
        try:
            callback = json.loads(body_str)
        except (json.JSONDecodeError, TypeError):
             if isinstance(body_str, bytes):
                callback = json.loads(body_str.decode('utf-8'))
             else:
                raise ValueError("Invalid callback body type")
            
        challenge = callback.get('challenge')
        if challenge:
             logger.info("Webhook challenge received")
             return True, challenge # IntaSend webhook verification

        # The core fields from IntaSend webhook payload
        invoice_id = callback.get('invoice_id')
        tracking_id = callback.get('tracking_id')
        state = callback.get('state') # COMPLETE, FAILED, PROCESSING, etc.
        value = callback.get('value')
        account = callback.get('account') 
        api_ref = callback.get('api_ref') # Our injected reference
        
        logger.info(f"Processing IntaSend webhook. Invoice: {invoice_id}, Tracking: {tracking_id}, State: {state}")
        
        # 1. Processing Collection / Deposit (STK Push)
        if invoice_id:
            try:
                # We saved invoice_id as mpesa_checkout_request_id
                escrow = Escrow.objects.get(mpesa_checkout_request_id=invoice_id)
            except Escrow.DoesNotExist:
                # Fallback to API Ref if we passed PROJ-{id}
                if api_ref and api_ref.startswith('PROJ-'):
                    project_id = api_ref.replace('PROJ-', '')
                    try:
                        contract = Contract.objects.get(project_id=project_id)
                        escrow = Escrow.objects.get(contract=contract)
                        # Patch it
                        escrow.mpesa_checkout_request_id = invoice_id
                        escrow.save()
                    except (Contract.DoesNotExist, Escrow.DoesNotExist):
                        logger.error(f"Escrow record not found for invoice: {invoice_id}")
                        return False, "Escrow record not found"
                else:
                    return False, "Escrow record not found and no valid api_ref"

            if state == 'COMPLETE':
                escrow.status = 'held'
                escrow.mpesa_receipt = callback.get('provider_reference') or "INTASEND-SUCCESS"
                escrow.save()

                contract = escrow.contract
                contract.payment_status = 'escrowed'
                contract.save()
                
                project = contract.project
                if project.status == 'assigned':
                    project.status = 'in_progress'
                    project.save()

                send_payment_notification(escrow, 'payment_deposited', contract.client)
                logger.info(f"Escrow {escrow.id} funds held successfully via IntaSend")
                return True, "Deposit processed successfully"
                
            elif state in ['FAILED', 'EXPIRED', 'CANCELLED']:
                escrow.status = 'failed'
                escrow.save()
                logger.warning(f"Escrow {escrow.id} deposit failed. State: {state}")
                return False, f"Deposit {state}"

        # 2. Processing Payout / Release (B2C)
        elif tracking_id:
            try:
                escrow = Escrow.objects.get(mpesa_conversation_id=tracking_id)
            except Escrow.DoesNotExist:
                logger.error(f"Escrow record not found for tracking ID: {tracking_id}")
                return False, "Escrow record not found"

            if state in ['COMPLETE', 'SUCCESSFUL']:
                escrow.status = 'released'
                escrow.mpesa_release_receipt = callback.get('provider_reference') or "INTASEND-RELEASE"
                escrow.released_at = timezone.now()
                escrow.save()

                contract = escrow.contract
                contract.payment_status = 'released'
                contract.status = 'completed'
                contract.completed_at = timezone.now()
                contract.save()

                project = contract.project
                project.status = 'completed'
                project.save()

                send_payment_notification(escrow, 'payment_released', contract.freelancer)
                logger.info(f"Escrow {escrow.id} funds released successfully via IntaSend")
                return True, "Funds released successfully"
                
            elif state in ['FAILED', 'REVERSED']:
                # The funds failed to send, they are technically still held by IntaSend/Us.
                escrow.status = 'held' 
                escrow.save()
                logger.warning(f"Escrow {escrow.id} release failed. State: {state}")
                return False, f"Release {state}"

        return True, "Webhook received but State/Type ignored"

    except Exception as e:
        logger.exception(f"Error processing IntaSend webhook: {str(e)}")
        return False, str(e)