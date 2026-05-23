from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny
from django.http import FileResponse, StreamingHttpResponse
from django.utils import timezone
from django.conf import settings
from django.db import transaction
from django.core.files.storage import default_storage
from core.authentication import JWTAuthentication
from core.models import Project, Contract, Escrow, Deliverable
from core.serializers import (
    ContractSerializer, ContractSignSerializer, EscrowDepositSerializer,
    DeliverableSerializer, DeliverableCreateSerializer, EscrowSerializer
)
from core.intasend_gateway import (
    initiate_escrow_deposit,
    release_escrow_funds,
)
from core.escrow_sync import process_econfirm_webhook, sync_escrow_from_provider
from core.mpesa_callbacks import process_intasend_webhook
from core.notification_service import (
    send_contract_notification, send_payment_notification, 
    send_deliverable_notification, send_project_notification
)
import logging
import os
import json
import mimetypes
import requests
from core.utils import format_phone_number

logger = logging.getLogger(__name__)


def _cloudinary_enabled():
    return bool(os.getenv('CLOUDINARY_URL', '').strip())


def _upload_deliverable_file(uploaded_file, contract):
    filename = os.path.basename(uploaded_file.name)

    if _cloudinary_enabled():
        import cloudinary
        import cloudinary.uploader

        cloudinary.config(secure=True)
        folder = os.getenv('CLOUDINARY_FOLDER', 'gigway/deliverables').strip('/ ')
        upload_result = cloudinary.uploader.upload(
            uploaded_file,
            resource_type='auto',
            folder=f"{folder}/{contract.id}",
            use_filename=True,
            unique_filename=True,
        )
        return {
            'storage': 'cloudinary',
            'file_url': upload_result.get('secure_url'),
            'public_id': upload_result.get('public_id'),
            'resource_type': upload_result.get('resource_type'),
            'original_filename': filename,
            'bytes': upload_result.get('bytes'),
            'format': upload_result.get('format'),
        }

    from django.core.files.base import ContentFile

    path = default_storage.save(
        f"deliverables/{contract.id}/{filename}",
        ContentFile(uploaded_file.read())
    )
    return {
        'storage': 'local',
        'file_url': path,
        'original_filename': filename,
    }


def _sync_escrow_from_provider(escrow):
    return sync_escrow_from_provider(escrow)

class ContractSignView(APIView):
    authentication_classes = [JWTAuthentication]

    def post(self, request, contract_id):
        try:
            contract = Contract.objects.get(id=contract_id)
            
            # Authorization check
            if request.user not in [contract.project.client, contract.project.freelancer]:
                return Response({'error': 'Not authorized'}, status=status.HTTP_403_FORBIDDEN)

            serializer = ContractSignSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            signature = serializer.validated_data['signature']

            if request.user == contract.project.client:
                if contract.client_signature:
                     return Response({'error': 'Already signed by client'}, status=status.HTTP_400_BAD_REQUEST)
                contract.client_signature = signature
                contract.client_signed_at = timezone.now()
            else:
                if contract.freelancer_signature:
                     return Response({'error': 'Already signed by freelancer'}, status=status.HTTP_400_BAD_REQUEST)
                contract.freelancer_signature = signature
                contract.freelancer_signed_at = timezone.now()

            # Check if both signed
            if contract.client_signature and contract.freelancer_signature:
                contract.status = 'signed'
                # Trigger Deposit UI prompt via notification/status update
            
            contract.save()
            
            # Notifications
            recipient = contract.project.freelancer if request.user == contract.project.client else contract.project.client
            send_contract_notification(contract, 'contract_signed', recipient)

            return Response(ContractSerializer(contract).data, status=status.HTTP_200_OK)

        except Contract.DoesNotExist:
            return Response({'error': 'Contract not found'}, status=status.HTTP_404_NOT_FOUND)

class EscrowDepositInitiateView(APIView):
    authentication_classes = [JWTAuthentication]

    def post(self, request):
        serializer = EscrowDepositSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        contract_id = serializer.validated_data['contract_id']

        try:
            contract = Contract.objects.get(id=contract_id)
            project = contract.project

            # Only client can initiate deposit?
            # User said: "Phase 2: Escrow Deposit (Client Side)"
            if request.user != project.client:
                return Response({'error': 'Only client can initiate deposit'}, status=status.HTTP_403_FORBIDDEN)

            if contract.status != 'signed':
                return Response({'error': 'Contract must be fully signed first'}, status=status.HTTP_400_BAD_REQUEST)
            if float(contract.amount) < 100:
                return Response({'error': 'Minimum escrow amount is KSh 100'}, status=status.HTTP_400_BAD_REQUEST)

            # Retrieve phone from profile
            phone_number = request.user.phone_number
            if not phone_number:
                 return Response({'error': 'Phone number missing in profile'}, status=status.HTTP_400_BAD_REQUEST)
            if not project.freelancer or not project.freelancer.phone_number:
                return Response({'error': 'Freelancer phone number missing for escrow receiver'}, status=status.HTTP_400_BAD_REQUEST)
            
            # Validate format (Kenyan)
            formatted_phone = format_phone_number(phone_number)
            if not formatted_phone.startswith('254'):
                 return Response({'error': 'Phone number must be a Kenyan number (254...)'}, status=status.HTTP_400_BAD_REQUEST)

            # Create or Get Escrow
            # Ensure idempotent
            escrow, created = Escrow.objects.get_or_create(
                contract=contract,
                defaults={
                    'amount': contract.amount,
                    'status': 'pending'
                }
            )
            
            if escrow.status in ['held', 'released', 'releasing']:
                 return Response({'message': 'Funds already in escrow', 'status': escrow.status}, status=status.HTTP_200_OK)

            # Initiate eConfirm escrow transaction + STK Push
            try:
                checkout_id = initiate_escrow_deposit(
                    phone_number=formatted_phone,
                    amount=float(contract.amount),
                    account_reference=f"PROJ-{project.id}",
                    buyer_email=project.client.email,
                    seller_email=project.freelancer.email if project.freelancer else None,
                    receiver_phone=project.freelancer.phone_number,
                    description=f"Escrow for project {project.id}",
                    terms="Funds are released upon deliverable approval by client.",
                )
                
                escrow.mpesa_checkout_request_id = checkout_id
                escrow.save()
                
                return Response({
                    'message': 'Escrow created and STK Push initiated. Check your phone.',
                    'checkout_request_id': checkout_id,
                    'status': 'pending'
                }, status=status.HTTP_200_OK)
                
            except Exception as e:
                logger.exception("STK Push Failed")
                return Response({'error': f"STK Push Failed: {str(e)}"}, status=status.HTTP_502_BAD_GATEWAY)

        except Contract.DoesNotExist:
            return Response({'error': 'Contract not found'}, status=status.HTTP_404_NOT_FOUND)

class DeliverableSubmissionView(APIView):
    authentication_classes = [JWTAuthentication]

    def post(self, request, contract_id):
        try:
            contract = Contract.objects.get(id=contract_id)
            
            if request.user != contract.project.freelancer:
                return Response({'error': 'Only assigned freelancer can submit'}, status=status.HTTP_403_FORBIDDEN)

            # Check if deliverables unlocked (Escrow must be held)
            # User says: "Phase 3... Trigger: Escrow deposit confirmed"
            if contract.payment_status != 'escrowed':
                # Try one live sync in case payment was just funded.
                try:
                    if hasattr(contract, 'escrow'):
                        _sync_escrow_from_provider(contract.escrow)
                        contract.refresh_from_db()
                except Exception as e:
                    logger.error(f"Deliverable precheck sync failed: {str(e)}")

                if contract.payment_status != 'escrowed':
                    return Response({'error': 'Cannot submit deliverables. Funds not yet in escrow.'}, status=status.HTTP_400_BAD_REQUEST)

            submission_type = request.data.get('submission_type', 'file')
            description = request.data.get('description', '')
            
            uploaded_file = request.FILES.get('file')
            file_url = request.data.get('file_url', '')
            content = request.data.get('content', '')
            
            data_to_store = {
                'submission_type': submission_type,
                'content': content,
                'file_url': file_url
            }
            if uploaded_file:
                data_to_store.update(_upload_deliverable_file(uploaded_file, contract))

            deliverable = Deliverable.objects.create(
                contract=contract,
                description=description,
                file_paths=json.dumps(data_to_store),
                status='submitted'
            )
            
            # Update Contract/Project status
            contract.status = 'deliverables_submitted'
            contract.save()
            contract.project.status = 'in_progress' # or review?
            contract.project.save()

            # Notify Client
            send_deliverable_notification(deliverable, 'deliverable_submitted')
            
            return Response(DeliverableSerializer(deliverable).data, status=status.HTTP_201_CREATED)

        except Contract.DoesNotExist:
             return Response({'error': 'Contract not found'}, status=status.HTTP_404_NOT_FOUND)

class DeliverableReviewView(APIView):
    authentication_classes = [JWTAuthentication]

    def post(self, request, deliverable_id):
        # Action: approve or reject
        action = request.data.get('action') # 'approve' or 'reject'
        
        try:
            deliverable = Deliverable.objects.get(id=deliverable_id)
            contract = deliverable.contract
            
            if request.user != contract.project.client:
                 return Response({'error': 'Only client can review'}, status=status.HTTP_403_FORBIDDEN)
            
            if action == 'approve':
                # User says: "Trigger: Client reviews... Approve... Immediate M-Pesa B2C Transfer"
                
                # Check Escrow Status
                if not hasattr(contract, 'escrow') or contract.escrow.status != 'held':
                    return Response({'error': 'No funds in escrow to release'}, status=status.HTTP_400_BAD_REQUEST)
                
                escrow = contract.escrow
                
                # Retrieve Freelancer Phone
                freelancer = contract.project.freelancer
                if not freelancer or not freelancer.phone_number:
                     return Response({'error': 'Freelancer phone number not found'}, status=status.HTTP_400_BAD_REQUEST)
                
                formatted_phone = format_phone_number(freelancer.phone_number)
                
                # Update status to local 'approved' first?
                # User says: "Client clicks Approve... Immediate B2C... Handle Callback -> Update Status"
                # So we shouldn't mark as released yet.
                
                # Double check status to prevent double pay
                if escrow.status == 'releasing':
                     return Response({'error': 'Release already in progress'}, status=status.HTTP_400_BAD_REQUEST)
                if not escrow.mpesa_checkout_request_id:
                    return Response({'error': 'Missing escrow transaction reference'}, status=status.HTTP_400_BAD_REQUEST)

                try:
                    # Refresh from provider to capture confirmation code if available.
                    try:
                        escrow = _sync_escrow_from_provider(escrow)
                    except Exception as e:
                        logger.warning(f"Could not refresh confirmation code before release: {str(e)}")

                    confirmation_code = request.data.get('confirmation_code') or escrow.confirmation_code
                    if not confirmation_code:
                        return Response(
                            {'error': 'Missing confirmation code. Enter the M-Pesa confirmation code from the payment SMS.'},
                            status=status.HTTP_400_BAD_REQUEST
                        )

                    # Release held funds using eConfirm transaction id
                    tracking_id = release_escrow_funds(
                        escrow.mpesa_checkout_request_id,
                        confirmation_code=confirmation_code,
                        notes='Client approved delivery'
                    )
                    
                    # Store Conversation ID (Tracking ID)
                    escrow.mpesa_conversation_id = tracking_id
                    escrow.confirmation_code = confirmation_code
                    escrow.status = 'releasing'
                    escrow.release_initiated_at = timezone.now()
                    escrow.save()
                    
                    deliverable.status = 'approved'
                    deliverable.approved = True
                    deliverable.approved_at = timezone.now()
                    deliverable.save()
                    
                    return Response({'message': 'Approval recorded. Payment release initiated.', 'status': 'releasing'}, status=status.HTTP_200_OK)
                    
                except Exception as e:
                    logger.exception("B2C Failed")
                    return Response({'error': f"Payment release failed: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

            elif action == 'reject':
                reason = request.data.get('reason')
                if not reason:
                     return Response({'error': 'Reason required for rejection'}, status=status.HTTP_400_BAD_REQUEST)
                
                deliverable.status = 'rejected'
                deliverable.rejection_reason = reason
                deliverable.save()
                
                send_deliverable_notification(deliverable, 'deliverable_rejected')
                return Response({'message': 'Deliverable rejected'}, status=status.HTTP_200_OK)
            
            else:
                 return Response({'error': 'Invalid action'}, status=status.HTTP_400_BAD_REQUEST)

        except Deliverable.DoesNotExist:
             return Response({'error': 'Deliverable not found'}, status=status.HTTP_404_NOT_FOUND)

class DeliverableDownloadView(APIView):
    authentication_classes = [JWTAuthentication]

    def get(self, request, deliverable_id):
        try:
            deliverable = Deliverable.objects.get(id=deliverable_id)
            contract = deliverable.contract

            if request.user not in [contract.project.client, contract.project.freelancer]:
                return Response({'error': 'Not authorized'}, status=status.HTTP_403_FORBIDDEN)

            try:
                payload = json.loads(deliverable.file_paths or '{}')
            except (TypeError, ValueError):
                payload = {}

            if payload.get('submission_type') != 'file':
                return Response({'error': 'This deliverable is not a file upload.'}, status=status.HTTP_400_BAD_REQUEST)

            file_path = str(payload.get('file_url') or '').strip()
            if not file_path:
                return Response({'error': 'Deliverable file is missing.'}, status=status.HTTP_404_NOT_FOUND)

            filename = payload.get('original_filename') or os.path.basename(file_path) or 'deliverable-file'
            content_type = mimetypes.guess_type(filename)[0] or 'application/octet-stream'

            if payload.get('storage') == 'cloudinary':
                upstream = requests.get(file_path, stream=True, timeout=20)
                if upstream.status_code != 200:
                    return Response(
                        {'error': 'Cloud deliverable file could not be retrieved. Please try again shortly.'},
                        status=status.HTTP_502_BAD_GATEWAY
                    )
                response = StreamingHttpResponse(
                    upstream.iter_content(chunk_size=8192),
                    content_type=upstream.headers.get('content-type') or content_type
                )
                response['Content-Disposition'] = f'attachment; filename="{filename}"'
                content_length = upstream.headers.get('content-length')
                if content_length:
                    response['Content-Length'] = content_length
                return response

            if not default_storage.exists(file_path):
                return Response(
                    {
                        'error': (
                            'Deliverable file was not found on the server. If this was uploaded before persistent '
                            'storage was configured, ask the freelancer to resubmit the file.'
                        )
                    },
                    status=status.HTTP_404_NOT_FOUND
                )

            response = FileResponse(default_storage.open(file_path, 'rb'), content_type=content_type)
            response['Content-Disposition'] = f'attachment; filename="{filename}"'
            return response

        except Deliverable.DoesNotExist:
            return Response({'error': 'Deliverable not found'}, status=status.HTTP_404_NOT_FOUND)

class WorkflowMpesaDepositCallbackView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request):
        body = request.body
        # Log logic
        with open(os.path.join(settings.BASE_DIR, 'mpesa_debug.log'), 'a') as f:
             f.write(f"\n--- {timezone.now()} INTASEND WEBHOOK ---\n")
             f.write(body.decode('utf-8') if isinstance(body, bytes) else str(body) + "\n")

        success, msg = process_intasend_webhook(body)
        if not success or 'ignored' in str(msg).lower():
            success, msg = process_econfirm_webhook(body)
        return Response({'result': msg}, status=status.HTTP_200_OK)

class WorkflowMpesaReleaseCallbackView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request):
        return Response({'result': 'Legacy tracking. Handled by unified webhook endpoint'}, status=status.HTTP_200_OK)

class EscrowStatusView(APIView):
    authentication_classes = [JWTAuthentication]

    def get(self, request, project_id):
        try:
            contract = Contract.objects.get(project_id=project_id)
            escrow = Escrow.objects.get(contract=contract)
            
            # Auto-sync with eConfirm each status fetch
            try:
                escrow = _sync_escrow_from_provider(escrow)
            except Exception as e:
                logger.error(f"Failed to sync escrow status: {str(e)}")

            return Response({
                'status': escrow.status,
                'amount': escrow.amount,
                'checkout_id': escrow.mpesa_checkout_request_id,
                'confirmation_code': escrow.confirmation_code
            }, status=status.HTTP_200_OK)
            
        except (Contract.DoesNotExist, Escrow.DoesNotExist):
            return Response({'error': 'Escrow not found'}, status=status.HTTP_404_NOT_FOUND)
