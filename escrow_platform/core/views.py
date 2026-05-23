from rest_framework.views import APIView
import os
import random
from decimal import Decimal, ROUND_HALF_UP
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny
from django.contrib.auth.hashers import make_password
from django.utils import timezone
from django.utils.dateparse import parse_datetime
from datetime import timedelta
from django.db.models import Q
from django.conf import settings
from core.serializers import (
    UserRegistrationSerializer, UserLoginSerializer, UserSerializer, UserProfileSerializer,
    ContractSerializer, ContractSignSerializer,
    EscrowDepositSerializer, EscrowSerializer, # Removed EscrowTransactionSerializer
    ProjectCreateSerializer, ProjectSerializer, DeliverableSerializer,
    DeliverableCreateSerializer, DisputeSerializer, DisputeCreateSerializer,
    ProposalSerializer, NotificationPreferenceSerializer, NotificationSerializer,
    SkillAssessmentQuestionSerializer, SkillAssessmentAttemptSerializer, VerifiedSkillSerializer,
    WorkHistorySerializer
)
# from core.mpesa_callbacks import process_deposit_callback, process_b2c_callback # Now in workflow_views
from django.http import HttpResponse, JsonResponse
import json
import logging
from core.utils import generate_jwt_token, decode_jwt_token
from core.authentication import JWTAuthentication
from core.models import (
    CustomUser, Project, Contract, Escrow, Dispute, Deliverable, Proposal,
    NotificationPreference, Notification, Milestone, SkillAssessmentQuestion,
    SkillAssessmentAttempt, SkillAssessmentAnswer, VerifiedSkill, WorkHistory
)
from core.contract_generator import generate_contract_text
from core.escrow_sync import sync_escrow_from_provider
from core.freelancer_readiness import calculate_freelancer_readiness
# from core.mpesa_b2c import send_b2c_payment, release_escrow_funds # cleanup
from core.dispute_analyzer import analyze_dispute_simple
from core.ai_dispute_analyzer import (
    analyze_dispute_with_ai,
    build_project_dispute_context,
    get_lexa_response,
)
from core.social_auth import authenticate_social_user
from core.notification_service import (
    send_project_notification, send_payment_notification, 
    send_deliverable_notification, send_dispute_notification,
    send_contract_notification, send_proposal_notification
)
from core.proposal_ai import generate_proposal_prefill

logger = logging.getLogger(__name__)


def create_contract_milestones(contract, proposal_amount):
    """Create read-only payment schedule rows without touching escrow payment flow."""
    project = contract.project
    if project.payment_mode != 'milestone':
        return

    plan = project.milestone_plan or []
    if not plan:
        return

    project_budget = Decimal(str(project.budget or 0))
    contract_amount = Decimal(str(proposal_amount or contract.amount or 0))
    if project_budget <= 0 or contract_amount <= 0:
        return

    running_total = Decimal('0.00')
    last_index = len(plan) - 1

    for index, item in enumerate(plan):
        if index == last_index:
            amount = contract_amount - running_total
        else:
            original_amount = Decimal(str(item.get('amount') or 0))
            amount = ((original_amount / project_budget) * contract_amount).quantize(
                Decimal('0.01'),
                rounding=ROUND_HALF_UP,
            )
            running_total += amount

        Milestone.objects.create(
            contract=contract,
            title=item.get('title') or f"Milestone {index + 1}",
            description=item.get('description') or '',
            amount=amount,
            due_date=item.get('due_date') or None,
            order=item.get('order') or index + 1,
        )

# Authentication Views
class RegisterView(APIView):
    def post(self, request):
        serializer = UserRegistrationSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        user = serializer.save()
        token = generate_jwt_token(user)
        
        return Response({
            'user': UserSerializer(user).data,
            'token': token
        }, status=status.HTTP_201_CREATED)

class LoginView(APIView):
    def post(self, request):
        serializer = UserLoginSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        user = serializer.validated_data['user']
        if not user.is_active:
            return Response({'error': 'Account disabled'}, status=status.HTTP_401_UNAUTHORIZED)
        
        token = generate_jwt_token(user)
        return Response({
            'user': UserSerializer(user).data,
            'token': token
        }, status=status.HTTP_200_OK)

class LogoutView(APIView):
    authentication_classes = [JWTAuthentication]
    
    def post(self, request):
        return Response({'message': 'Successfully logged out'}, status=status.HTTP_200_OK)

class SocialAuthView(APIView):
    """Handle social authentication (Google, Facebook)"""
    permission_classes = [AllowAny]
    
    def post(self, request):
        provider = request.data.get('provider')
        access_token = request.data.get('access_token')
        code = request.data.get('code')
        redirect_uri = request.data.get('redirect_uri')
        phone_number = request.data.get('phone_number')
        
        if not provider or (not access_token and not code):
            return Response({'error': 'provider and either access_token or code are required'}, status=status.HTTP_400_BAD_REQUEST)
        
        if provider not in ['google', 'facebook']:
            return Response({'error': 'Unsupported provider'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            result = authenticate_social_user(
                provider=provider,
                access_token=access_token,
                phone_number=phone_number,
                code=code,
                redirect_uri=redirect_uri
            )
            user = CustomUser.objects.get(id=result['user']['id'])
            return Response({
                'user': UserSerializer(user).data,
                'token': result['token'],
                'created': result['created'],
                'message': 'Account created' if result['created'] else 'Login successful'
            }, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_401_UNAUTHORIZED)

class UserProfileView(APIView):
    authentication_classes = [JWTAuthentication]

    def get(self, request):
        if not request.user or not request.user.is_authenticated:
            return Response({'error': 'Authentication required'}, status=status.HTTP_401_UNAUTHORIZED)
        return Response(UserSerializer(request.user).data, status=status.HTTP_200_OK)

    def patch(self, request):
        user = request.user
        if not user or not user.is_authenticated:
            return Response({'error': 'Authentication required'}, status=status.HTTP_401_UNAUTHORIZED)
        serializer = UserProfileSerializer(user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(UserSerializer(user).data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class ChangePasswordView(APIView):
    authentication_classes = [JWTAuthentication]

    def post(self, request):
        user = request.user
        current_password = request.data.get('current_password')
        new_password = request.data.get('new_password')

        if not current_password or not new_password:
            return Response({'error': 'current_password and new_password are required'}, status=status.HTTP_400_BAD_REQUEST)

        if not user.check_password(current_password):
            return Response({'error': 'Current password is incorrect'}, status=status.HTTP_400_BAD_REQUEST)

        if len(new_password) < 8:
            return Response({'error': 'New password must be at least 8 characters long'}, status=status.HTTP_400_BAD_REQUEST)

        user.set_password(new_password)
        user.save()
        return Response({'message': 'Password changed successfully'}, status=status.HTTP_200_OK)

class WalletView(APIView):
    authentication_classes = [JWTAuthentication]

    def get(self, request):
        user = request.user

        if user.user_type == 'freelancer':
            contracts = Contract.objects.filter(freelancer=user).select_related('project', 'escrow')
        else:
            contracts = Contract.objects.filter(client=user).select_related('project', 'escrow')

        transactions = []
        in_escrow = Decimal('0.00')
        total_earnings = Decimal('0.00')

        for contract in contracts:
            try:
                escrow = contract.escrow
            except Escrow.DoesNotExist:
                continue

            try:
                escrow = sync_escrow_from_provider(escrow)
                contract.refresh_from_db()
            except Exception as e:
                logger.warning("Wallet escrow sync failed for %s: %s", escrow.id, str(e))

            escrow_status = escrow.status
            payment_status = contract.payment_status

            if escrow_status in ['held', 'releasing'] or payment_status == 'escrowed':
                in_escrow += escrow.amount
            if escrow_status == 'released' or payment_status == 'released':
                total_earnings += escrow.amount

            transactions.append({
                'id': str(escrow.id),
                'project_title': contract.project.title,
                'amount': escrow.amount,
                'status': escrow_status,
                'payment_status': payment_status,
                'date': escrow.released_at or escrow.created_at or contract.project.created_at,
                'receipt': escrow.mpesa_release_receipt or escrow.mpesa_receipt or escrow.confirmation_code
            })

        return Response({
            'in_escrow': in_escrow,
            'total_earnings': total_earnings,
            'transactions': transactions
        })

class ProjectViewSet(APIView):
    authentication_classes = [JWTAuthentication]

    def get_queryset(self, user):
        view = self.request.query_params.get('view', 'my_projects')
        queryset = Project.objects.none()

        if user.user_type == 'client':
            queryset = Project.objects.filter(client=user)
        elif user.user_type == 'freelancer':
            if view == 'find_work':
                queryset = Project.objects.filter(status='open')
            else:
                queryset = Project.objects.filter(freelancer=user)
        
        search = self.request.query_params.get('search')
        if search:
            queryset = queryset.filter(Q(title__icontains=search) | Q(description__icontains=search))
        
        min_budget = self.request.query_params.get('min_budget')
        if min_budget:
            queryset = queryset.filter(budget__gte=min_budget)
            
        max_budget = self.request.query_params.get('max_budget')
        if max_budget:
            queryset = queryset.filter(budget__lte=max_budget)
            
        return queryset

    def post(self, request):
        if request.user.user_type != 'client':
            return Response({'error': 'Only clients can create projects'}, status=status.HTTP_403_FORBIDDEN)
        
        try:
            serializer = ProjectCreateSerializer(data=request.data, context={'request': request})
            serializer.is_valid(raise_exception=True)
            project = serializer.save()
            
            # Create pending contract
            try:
                # Assuming contract is created on project assignment? Or now?
                # User flow: Proposal -> Assign -> Contract Sign.
                # Project creation adds project. No contract yet until assigned?
                # But creating a blank contract when project is assigned is good.
                pass
            except Exception:
                pass

            send_project_notification(project, 'project_created')
            return Response(ProjectSerializer(project).data, status=status.HTTP_201_CREATED)
        except Exception as e:
            import traceback
            traceback.print_exc()
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def get(self, request, project_id=None):
        if project_id:
            try:
                project = Project.objects.get(id=project_id)
                is_owner = project.client == request.user
                is_assigned = project.freelancer == request.user
                is_open_for_freelancer = project.status == 'open' and request.user.user_type == 'freelancer'
                
                if not (is_owner or is_assigned or is_open_for_freelancer):
                    return Response({'error': 'Not authorized'}, status=status.HTTP_403_FORBIDDEN)
                if hasattr(project, 'contract') and hasattr(project.contract, 'escrow'):
                    try:
                        sync_escrow_from_provider(project.contract.escrow)
                        project.refresh_from_db()
                    except Exception as e:
                        logger.error(f"Project escrow sync failed: {str(e)}")
                return Response(ProjectSerializer(project).data)
            except Project.DoesNotExist:
                return Response({'error': 'Project not found'}, status=status.HTTP_404_NOT_FOUND)
        
        projects = self.get_queryset(request.user)
        serializer = ProjectSerializer(projects, many=True)
        return Response(serializer.data)

    def patch(self, request, project_id):
        try:
            project = Project.objects.get(id=project_id)
            if project.client != request.user:
                return Response({'error': 'Only project owner can update'}, status=status.HTTP_403_FORBIDDEN)
            
            serializer = ProjectSerializer(project, data=request.data, partial=True)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data)
        except Project.DoesNotExist:
            return Response({'error': 'Project not found'}, status=status.HTTP_404_NOT_FOUND)

    def delete(self, request, project_id):
        try:
            project = Project.objects.get(id=project_id)
            if project.client != request.user:
                return Response({'error': 'Only project owner can delete'}, status=status.HTTP_403_FORBIDDEN)
            if project.status != 'open':
                return Response({'error': 'Can only delete open projects'}, status=status.HTTP_400_BAD_REQUEST)
            project.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except Project.DoesNotExist:
            return Response({'error': 'Project not found'}, status=status.HTTP_404_NOT_FOUND)

class ContractView(APIView):
    authentication_classes = [JWTAuthentication]

    def get(self, request, project_id):
        try:
            project = Project.objects.get(id=project_id)
            if project.client != request.user and project.freelancer != request.user:
                return Response({'error': 'Not authorized'}, status=status.HTTP_403_FORBIDDEN)
            
            try:
                # Contract is OneToOne on Project now
                if hasattr(project, 'contract'):
                    return Response(ContractSerializer(project.contract).data)
                else:
                    return Response({'error': 'Contract not found'}, status=status.HTTP_404_NOT_FOUND)
            except Exception: # Handling if relation doesn't exist
                 return Response({'error': 'Contract not found'}, status=status.HTTP_404_NOT_FOUND)
                
        except Project.DoesNotExist:
            return Response({'error': 'Project not found'}, status=status.HTTP_404_NOT_FOUND)

    # POST removed - use ContractSignView in workflow_views.py

class DeliverableView(APIView):
    authentication_classes = [JWTAuthentication]

    def get(self, request, project_id=None):
        if project_id:
            try:
                project = Project.objects.get(id=project_id)
                if request.user not in [project.client, project.freelancer]:
                    return Response({'error': 'Not authorized'}, status=status.HTTP_403_FORBIDDEN)
                
                # Fetch deliverables via Contract
                if hasattr(project, 'contract'):
                    if hasattr(project.contract, 'escrow'):
                        try:
                            sync_escrow_from_provider(project.contract.escrow)
                        except Exception as e:
                            logger.error(f"Deliverables escrow sync failed: {str(e)}")
                    deliverables = Deliverable.objects.filter(contract=project.contract)
                    return Response(DeliverableSerializer(deliverables, many=True).data, status=status.HTTP_200_OK)
                else:
                    return Response([], status=status.HTTP_200_OK)
            except Project.DoesNotExist:
                return Response({'error': 'Project not found'}, status=status.HTTP_404_NOT_FOUND)
        else:
            # Maybe list all user's deliverables?
            return Response([], status=status.HTTP_200_OK)


# Other utility views (Dispute, Notification, etc.) - Preserved but simplified here for brevity if they don't break
class DisputeView(APIView):
    authentication_classes = [JWTAuthentication]
    def get(self, request, project_id=None):
        queryset = Dispute.objects.filter(Q(project__client=request.user) | Q(project__freelancer=request.user))
        if project_id:
            queryset = queryset.filter(project_id=project_id)
        return Response(DisputeSerializer(queryset, many=True).data)

    def post(self, request):
        serializer = DisputeCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        project = Project.objects.get(id=serializer.validated_data['project_id'])
        if request.user not in [project.client, project.freelancer]:
            return Response({'error': 'Not authorized'}, status=status.HTTP_403_FORBIDDEN)

        dispute = Dispute.objects.create(
            project=project,
            raised_by=request.user,
            reason=serializer.validated_data['reason'],
            evidence_url=request.data.get('evidence_url') or request.data.get('evidence_file') or '',
        )
        project.status = 'disputed'
        project.save(update_fields=['status'])
        send_dispute_notification(dispute, 'dispute_raised')
        return Response(DisputeSerializer(dispute).data, status=status.HTTP_201_CREATED)

class DisputeAnalyzeView(APIView):
    authentication_classes = [JWTAuthentication]
    def post(self, request, dispute_id):
        try:
            dispute = Dispute.objects.get(id=dispute_id)
            if request.user not in [dispute.project.client, dispute.project.freelancer]:
                return Response({'error': 'Not authorized'}, status=status.HTTP_403_FORBIDDEN)

            analysis = analyze_dispute_with_ai(str(dispute_id))
            dispute.ai_recommendation = analysis
            dispute.status = 'under_review'
            dispute.save(update_fields=['ai_recommendation', 'status'])
            return Response({'status': 'analyzed', 'analysis': analysis})
        except Dispute.DoesNotExist:
            return Response({'error': 'Dispute not found'}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.exception("Failed to analyze dispute")
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class DisputeResolveView(APIView):
    authentication_classes = [JWTAuthentication]
    def post(self, request, dispute_id):
         return Response({'status': 'resolved'})

class LexaChatView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    def _get_optional_user(self, request):
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return None

        payload = decode_jwt_token(auth_header.split(' ')[1])
        if 'error' in payload:
            logger.warning("Ignoring invalid Lexa auth token: %s", payload['error'])
            return None

        try:
            return CustomUser.objects.get(id=payload['user_id'], is_active=True)
        except CustomUser.DoesNotExist:
            logger.warning("Ignoring Lexa auth token for missing/inactive user: %s", payload.get('user_id'))
            return None

    def post(self, request):
        user = self._get_optional_user(request)
        message = request.data.get('message', '')
        project_id = request.data.get('project_id')
        message_lower = str(message).lower()

        if user and user.user_type == 'freelancer' and any(
            keyword in message_lower
            for keyword in ['competency', 'readiness', 'trust score', 'verified', 'verification', 'pass proposal', 'pass score']
        ):
            readiness = calculate_freelancer_readiness(user)
            next_actions = readiness.get('next_actions') or ['Apply only to jobs that match your skills and write a specific proposal.']
            response_text = (
                f"Your freelancer readiness score is {readiness['score']}% ({readiness['level'].replace('_', ' ')}). "
                "To pass competency checks, keep your profile aligned with the job, add real proof links, and write proposals that mention the client's actual requirements.\n\n"
                "Next steps:\n"
                + "\n".join(f"- {action}" for action in next_actions)
            )
            return Response({'reply': response_text})
        
        project_context = None
        if project_id:
            if not user:
                return Response({'error': 'Please log in again so I can access that project context.'}, status=status.HTTP_401_UNAUTHORIZED)
            try:
                project = Project.objects.get(id=project_id)
                if user not in [project.client, project.freelancer]:
                    return Response({'error': 'Not authorized for this project'}, status=status.HTTP_403_FORBIDDEN)
                project_context = build_project_dispute_context(project)
            except Project.DoesNotExist:
                return Response({'error': 'Project not found'}, status=status.HTTP_404_NOT_FOUND)

        try:
            response_text = get_lexa_response(message, project_context)
        except Exception as e:
            logger.exception("Lexa project chat failed")
            return Response({'error': f'Gemini request failed: {str(e)}'}, status=status.HTTP_502_BAD_GATEWAY)
        return Response({'reply': response_text})

class ProposalViewSet(APIView):
    authentication_classes = [JWTAuthentication]
    
    def get(self, request):
        project_id = request.query_params.get('project')
        if request.user.user_type == 'client':
            queryset = Proposal.objects.filter(project__client=request.user)
        else:
            queryset = Proposal.objects.filter(freelancer=request.user)
            
        if project_id:
            queryset = queryset.filter(project_id=project_id)
            
        serializer = ProposalSerializer(queryset, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        if request.user.user_type != 'freelancer':
            return Response({'error': 'Only freelancers can submit proposals'}, status=status.HTTP_403_FORBIDDEN)
            
        serializer = ProposalSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            try:
                # Basic check to avoid duplicates
                project_id = request.data.get('project')
                if Proposal.objects.filter(project_id=project_id, freelancer=request.user).exists():
                    return Response({'error': 'You already submitted a proposal for this project.'}, status=status.HTTP_400_BAD_REQUEST)
                
                proposal = serializer.save()
                send_proposal_notification(proposal, 'proposal_received')
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            except Exception as e:
                return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class WorkHistoryView(APIView):
    authentication_classes = [JWTAuthentication]

    def get(self, request, entry_id=None):
        if request.user.user_type != 'freelancer':
            return Response({'error': 'Only freelancers have work history.'}, status=status.HTTP_403_FORBIDDEN)
        queryset = WorkHistory.objects.filter(freelancer=request.user)
        serializer = WorkHistorySerializer(queryset, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        if request.user.user_type != 'freelancer':
            return Response({'error': 'Only freelancers can add work history.'}, status=status.HTTP_403_FORBIDDEN)
        serializer = WorkHistorySerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        entry = serializer.save()
        return Response(WorkHistorySerializer(entry).data, status=status.HTTP_201_CREATED)

    def patch(self, request, entry_id):
        if request.user.user_type != 'freelancer':
            return Response({'error': 'Only freelancers can update work history.'}, status=status.HTTP_403_FORBIDDEN)
        try:
            entry = WorkHistory.objects.get(id=entry_id, freelancer=request.user)
        except WorkHistory.DoesNotExist:
            return Response({'error': 'Work history entry not found.'}, status=status.HTTP_404_NOT_FOUND)
        serializer = WorkHistorySerializer(entry, data=request.data, partial=True, context={'request': request})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)

    def delete(self, request, entry_id):
        if request.user.user_type != 'freelancer':
            return Response({'error': 'Only freelancers can delete work history.'}, status=status.HTTP_403_FORBIDDEN)
        try:
            entry = WorkHistory.objects.get(id=entry_id, freelancer=request.user)
        except WorkHistory.DoesNotExist:
            return Response({'error': 'Work history entry not found.'}, status=status.HTTP_404_NOT_FOUND)
        entry.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

class ProposalPrefillView(APIView):
    authentication_classes = [JWTAuthentication]

    def post(self, request, project_id):
        if request.user.user_type != 'freelancer':
            return Response({'error': 'Only freelancers can generate proposal drafts.'}, status=status.HTTP_403_FORBIDDEN)
        try:
            project = Project.objects.get(id=project_id, status='open')
        except Project.DoesNotExist:
            return Response({'error': 'Open project not found.'}, status=status.HTTP_404_NOT_FOUND)

        work_history = WorkHistory.objects.filter(freelancer=request.user)
        try:
            result = generate_proposal_prefill(project, request.user, work_history)
        except ValueError as exc:
            return Response({'error': str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as exc:
            logger.exception("Proposal prefill failed")
            return Response({'error': f'Gemini proposal draft failed: {str(exc)}'}, status=status.HTTP_502_BAD_GATEWAY)
        return Response(result, status=status.HTTP_200_OK)

class AcceptProposalView(APIView):
    authentication_classes = [JWTAuthentication]
    def post(self, request, proposal_id):
        # Logic to accept proposal -> create Contract
        try:
            proposal = Proposal.objects.get(id=proposal_id)
            if request.user != proposal.project.client:
                 return Response({'error': 'Not authorized'}, status=status.HTTP_403_FORBIDDEN)
            
            proposal.status = 'accepted'
            proposal.save()
            proposal.project.freelancer = proposal.freelancer
            proposal.project.status = 'assigned'
            proposal.project.save()
            
            # Generate dynamic contract text
            contract_text = generate_contract_text(proposal.project)
            if proposal.bid_amount < 100:
                return Response({'error': 'Minimum escrow amount is KSh 100'}, status=status.HTTP_400_BAD_REQUEST)
            
            # Create Contract
            contract = Contract.objects.create(
                project=proposal.project,
                client=proposal.project.client,
                freelancer=proposal.freelancer,
                amount=proposal.bid_amount, # Or project budget
                contract_text=contract_text,
                status='pending_signature',
                payment_status='pending'
            )
            create_contract_milestones(contract, proposal.bid_amount)
            
            send_proposal_notification(proposal, 'proposal_accepted')
            return Response({'message': 'Proposal accepted, contract created'}, status=status.HTTP_200_OK)
            
        except Proposal.DoesNotExist:
             return Response({'error': 'Proposal not found'}, status=status.HTTP_404_NOT_FOUND)

class NotificationPreferenceView(APIView):
    authentication_classes = [JWTAuthentication]
    def get(self, request):
        return Response({}) # Placeholder

class NotificationListView(APIView):
    authentication_classes = [JWTAuthentication]
    def get(self, request):
        return Response([])

class MarkNotificationReadView(APIView):
    def post(self, request, notification_id):
        return Response({'status': 'read'})

class SkillAssessmentOptionsView(APIView):
    authentication_classes = [JWTAuthentication]

    def get(self, request):
        if request.user.user_type != 'freelancer':
            return Response({'error': 'Only freelancers can take skill tests'}, status=status.HTTP_403_FORBIDDEN)

        skills = [
            {'value': value, 'label': label}
            for value, label in SkillAssessmentQuestion.SKILL_CHOICES
            if SkillAssessmentQuestion.objects.filter(skill=value, is_active=True).exists()
        ]
        levels = [
            {'value': value, 'label': label}
            for value, label in SkillAssessmentQuestion.LEVEL_CHOICES
        ]
        verified = VerifiedSkill.objects.filter(user=request.user)
        return Response({
            'skills': skills,
            'levels': levels,
            'verified_skills': VerifiedSkillSerializer(verified, many=True).data,
        })

class SkillAssessmentStartView(APIView):
    authentication_classes = [JWTAuthentication]

    def post(self, request):
        if request.user.user_type != 'freelancer':
            return Response({'error': 'Only freelancers can take skill tests'}, status=status.HTTP_403_FORBIDDEN)

        skill = request.data.get('skill')
        level = request.data.get('level')
        if skill not in dict(SkillAssessmentQuestion.SKILL_CHOICES):
            return Response({'error': 'Choose a valid skill'}, status=status.HTTP_400_BAD_REQUEST)
        if level not in dict(SkillAssessmentQuestion.LEVEL_CHOICES):
            return Response({'error': 'Choose a valid level'}, status=status.HTTP_400_BAD_REQUEST)

        questions = list(SkillAssessmentQuestion.objects.filter(
            skill=skill,
            level=level,
            is_active=True,
        ))
        if len(questions) < 5:
            return Response({'error': 'Not enough approved questions for this test yet'}, status=status.HTTP_400_BAD_REQUEST)

        random.shuffle(questions)
        selected = questions[:min(10, len(questions))]

        SkillAssessmentAttempt.objects.filter(user=request.user, status='active').update(status='expired')
        attempt = SkillAssessmentAttempt.objects.create(
            user=request.user,
            skill=skill,
            level=level,
            question_ids=[str(question.id) for question in selected],
            total_questions=len(selected),
            question_started_at=timezone.now(),
        )

        return Response(_assessment_payload(attempt), status=status.HTTP_201_CREATED)

class SkillAssessmentAnswerView(APIView):
    authentication_classes = [JWTAuthentication]

    def post(self, request, attempt_id):
        try:
            attempt = SkillAssessmentAttempt.objects.get(id=attempt_id, user=request.user)
        except SkillAssessmentAttempt.DoesNotExist:
            return Response({'error': 'Assessment attempt not found'}, status=status.HTTP_404_NOT_FOUND)

        if attempt.status != 'active':
            return Response(_assessment_payload(attempt), status=status.HTTP_200_OK)

        timed_out = bool(request.data.get('timed_out', False))
        selected_choice = str(request.data.get('selected_choice') or '').strip().upper()
        elapsed_seconds = (timezone.now() - attempt.question_started_at).total_seconds()
        if elapsed_seconds > attempt.time_limit_seconds:
            timed_out = True
            selected_choice = ''

        question = _current_assessment_question(attempt)
        if not question:
            _complete_assessment(attempt)
            return Response(_assessment_payload(attempt), status=status.HTTP_200_OK)

        is_correct = (not timed_out) and selected_choice == question.correct_choice.upper()
        SkillAssessmentAnswer.objects.get_or_create(
            attempt=attempt,
            question=question,
            defaults={
                'selected_choice': selected_choice,
                'is_correct': is_correct,
                'timed_out': timed_out,
            }
        )

        if is_correct:
            attempt.correct_count += 1

        attempt.current_index += 1
        if attempt.current_index >= attempt.total_questions:
            _complete_assessment(attempt)
        else:
            attempt.question_started_at = timezone.now()
            attempt.save(update_fields=['current_index', 'correct_count', 'question_started_at'])

        return Response(_assessment_payload(attempt), status=status.HTTP_200_OK)


def _current_assessment_question(attempt):
    if attempt.current_index >= len(attempt.question_ids):
        return None
    question_id = attempt.question_ids[attempt.current_index]
    try:
        return SkillAssessmentQuestion.objects.get(id=question_id, is_active=True)
    except SkillAssessmentQuestion.DoesNotExist:
        return None


def _assessment_payload(attempt):
    question = _current_assessment_question(attempt) if attempt.status == 'active' else None
    payload = {
        'attempt': SkillAssessmentAttemptSerializer(attempt).data,
        'is_complete': attempt.status != 'active',
        'verified_skill': None,
        'question': None,
    }
    if question:
        payload['question'] = {
            **SkillAssessmentQuestionSerializer(question).data,
            'number': attempt.current_index + 1,
            'total': attempt.total_questions,
            'started_at': attempt.question_started_at.isoformat(),
            'time_limit_seconds': attempt.time_limit_seconds,
        }
    if attempt.status == 'completed':
        verified = VerifiedSkill.objects.filter(user=attempt.user, skill=attempt.skill, level=attempt.level).first()
        if verified:
            payload['verified_skill'] = VerifiedSkillSerializer(verified).data
    return payload


def _complete_assessment(attempt):
    attempt.status = 'completed'
    attempt.score = round((attempt.correct_count / max(1, attempt.total_questions)) * 100)
    attempt.completed_at = timezone.now()
    attempt.save(update_fields=['status', 'score', 'completed_at', 'current_index', 'correct_count'])

    verified, _ = VerifiedSkill.objects.get_or_create(
        user=attempt.user,
        skill=attempt.skill,
        level=attempt.level,
        defaults={'best_score': 0, 'last_score': 0}
    )
    verified.last_score = attempt.score
    verified.best_score = max(verified.best_score, attempt.score)
    verified.is_verified = verified.best_score >= 70
    if verified.is_verified:
        verified.verified_at = verified.verified_at or timezone.now()
        verified.expires_at = timezone.now() + timedelta(days=365)
    verified.save()
        
# Deprecated Views Removed:
# EscrowDepositView, MpesaCallbackView, MpesaReleaseCallbackView, DeliverableApproveView, DeliverableRejectView, EscrowStatusView
class EscrowStatusView(APIView): # Keep just in case frontend polls it
    authentication_classes = [JWTAuthentication]
    def get(self, request, project_id):
        # Return status
        try:
            project = Project.objects.get(id=project_id)
            if hasattr(project, 'contract') and hasattr(project.contract, 'escrow'):
                return Response({'status': project.contract.escrow.status})
            return Response({'status': 'none'})
        except Project.DoesNotExist:
            return Response({'status': 'error'}, status=status.HTTP_404_NOT_FOUND)
