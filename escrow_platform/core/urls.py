from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from rest_framework.decorators import api_view
from rest_framework.response import Response

# Import existing views
from core.views import (
    RegisterView, LoginView, LogoutView, SocialAuthView, WalletView, UserProfileView, 
    ChangePasswordView, ProjectViewSet, ContractView, 
    DisputeView, DisputeAnalyzeView, DisputeResolveView,
    LexaChatView, ProposalViewSet, AcceptProposalView,
    NotificationPreferenceView, NotificationListView, MarkNotificationReadView,
    DeliverableView,  # Keeping usage for listing if needed, or replace
    SkillAssessmentOptionsView, SkillAssessmentStartView, SkillAssessmentAnswerView
)

# Import NEW workflow views
from core.workflow_views import (
    ContractSignView, EscrowDepositInitiateView, 
    DeliverableSubmissionView, DeliverableReviewView,
    WorkflowMpesaDepositCallbackView, WorkflowMpesaReleaseCallbackView,
    EscrowStatusView
)

@api_view(['GET'])
def health_check(request):
    return Response({'status': 'ok'})

urlpatterns = [
    # System
    path('', health_check, name='root-health-check'),
    path('api/', health_check, name='api-root-health-check'),
    path('api/health/', health_check, name='health-check'),

    # Auth
    path('api/auth/register/', RegisterView.as_view(), name='register'),
    path('api/auth/login/', LoginView.as_view(), name='login'),
    path('api/auth/logout/', LogoutView.as_view(), name='logout'),
    path('api/auth/social/', SocialAuthView.as_view(), name='social-auth'),
    path('api/auth/profile/', UserProfileView.as_view(), name='user-profile'),
    path('api/auth/change-password/', ChangePasswordView.as_view(), name='change-password'),
    
    # Wallet / Dashboard
    path('api/wallet/', WalletView.as_view(), name='wallet'),

    # Projects
    path('api/projects/', ProjectViewSet.as_view(), name='project-list'),
    path('api/projects/<uuid:project_id>/', ProjectViewSet.as_view(), name='project-detail'),
    
    # Proposals
    path('api/proposals/', ProposalViewSet.as_view(), name='proposal-list'),
    path('api/proposals/<uuid:proposal_id>/accept/', AcceptProposalView.as_view(), name='proposal-accept'),

    # Contracts (View/Sign)
    path('api/projects/<uuid:project_id>/contract/', ContractView.as_view(), name='project-contract'), # Get Contract
    path('api/contract/<uuid:contract_id>/sign/', ContractSignView.as_view(), name='sign-contract'), # Sign Contract

    # Escrow
    path('api/escrow/deposit/', EscrowDepositInitiateView.as_view(), name='escrow-deposit'),
    path('api/escrow/status/<uuid:project_id>/', EscrowStatusView.as_view(), name='escrow-status'),
    
    # M-Pesa Callbacks (External)
    path('api/mpesa/callback/deposit/', WorkflowMpesaDepositCallbackView.as_view(), name='mpesa-deposit-callback'),
    path('api/mpesa/callback/deposit', WorkflowMpesaDepositCallbackView.as_view()), # Handle missing slash
    path('api/mpesa/callback/release/', WorkflowMpesaReleaseCallbackView.as_view(), name='mpesa-release-callback'),
    path('api/mpesa/callback/release', WorkflowMpesaReleaseCallbackView.as_view()),

    # Deliverables
    path('api/deliverables/', DeliverableView.as_view(), name='deliverable-list'), # List
    path('api/deliverables/<uuid:project_id>/', DeliverableView.as_view(), name='project-deliverables'), # List for project
    path('api/contract/<uuid:contract_id>/submit-deliverable/', DeliverableSubmissionView.as_view(), name='submit-deliverable'), # New: Submit
    path('api/deliverables/<uuid:deliverable_id>/review/', DeliverableReviewView.as_view(), name='review-deliverable'), # New: Approve/Reject

    # Disputes
    path('api/disputes/', DisputeView.as_view(), name='dispute-list'),
    path('api/disputes/<uuid:project_id>/', DisputeView.as_view(), name='project-disputes'),
    path('api/disputes/<uuid:dispute_id>/analyze/', DisputeAnalyzeView.as_view(), name='dispute-analyze'),
    path('api/disputes/<uuid:dispute_id>/resolve/', DisputeResolveView.as_view(), name='dispute-resolve'),

    # Lexa / AI
    path('api/lexa/chat/', LexaChatView.as_view(), name='lexa-chat'),
    path('api/lexa/skill-test/options/', SkillAssessmentOptionsView.as_view(), name='skill-test-options'),
    path('api/lexa/skill-test/start/', SkillAssessmentStartView.as_view(), name='skill-test-start'),
    path('api/lexa/skill-test/<uuid:attempt_id>/answer/', SkillAssessmentAnswerView.as_view(), name='skill-test-answer'),

    # Notifications
    path('api/notifications/preferences/', NotificationPreferenceView.as_view(), name='notification-preferences'),
    path('api/notifications/', NotificationListView.as_view(), name='notification-list'),
    path('api/notifications/<uuid:notification_id>/read/', MarkNotificationReadView.as_view(), name='notification-read'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
