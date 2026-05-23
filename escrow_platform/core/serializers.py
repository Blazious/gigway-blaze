from rest_framework import serializers
from decimal import Decimal
from core.models import (
    CustomUser, Project, Contract, Escrow, 
    Deliverable, Dispute, Proposal, NotificationPreference, Notification, Milestone,
    SkillAssessmentQuestion, SkillAssessmentAttempt, VerifiedSkill
)
from core.competency_verification import evaluate_freelancer_for_project
from core.freelancer_readiness import calculate_freelancer_readiness
from core.link_verification import validate_external_url
from core.utils import generate_jwt_token

class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)
    
    class Meta:
        model = CustomUser
        fields = ['email', 'password', 'phone_number', 'user_type']
        extra_kwargs = {
            'password': {'write_only': True}
        }

    def validate_email(self, value):
        if CustomUser.objects.filter(email=value).exists():
            raise serializers.ValidationError("Email already exists")
        return value

    def create(self, validated_data):
        user = CustomUser.objects.create_user(
            email=validated_data['email'],
            password=validated_data['password'],
            phone_number=validated_data['phone_number'],
            user_type=validated_data['user_type']
        )
        return user

class UserLoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate(self, data):
        email = data.get('email')
        password = data.get('password')

        if email and password:
            user = CustomUser.objects.filter(email=email).first()
            if user and user.check_password(password):
                data['user'] = user
                return data
            raise serializers.ValidationError("Invalid credentials")
        raise serializers.ValidationError("Email and password are required")

class UserSerializer(serializers.ModelSerializer):
    freelancer_readiness = serializers.SerializerMethodField()

    class Meta:
        model = CustomUser
        fields = ['id', 'email', 'phone_number', 'user_type', 'bio', 'profile_picture', 
                 'profession', 'skills', 'social_links', 'country', 'city', 'company_name',
                 'freelancer_readiness', 'created_at']
        read_only_fields = ['id', 'created_at']

    def get_freelancer_readiness(self, obj):
        return calculate_freelancer_readiness(obj)

class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ['phone_number', 'bio', 'profile_picture', 'profession', 'skills', 
                 'social_links', 'country', 'city', 'company_name']
        extra_kwargs = {
            'profile_picture': {'required': False}
        }

    def validate_skills(self, value):
        if isinstance(value, str):
            import json
            try:
                return json.loads(value)
            except ValueError:
                return []
        return value

    def validate_social_links(self, value):
        if isinstance(value, str):
            import json
            try:
                value = json.loads(value)
            except ValueError:
                return {}
        if not isinstance(value, dict):
            raise serializers.ValidationError("Social links must be an object.")

        cleaned = {}
        domain_rules = {
            'linkedin': {'linkedin.com'},
            'github': {'github.com'},
        }
        for key, link in value.items():
            if not link:
                cleaned[key] = ''
                continue
            allowed_domains = domain_rules.get(key)
            try:
                cleaned[key] = validate_external_url(
                    link,
                    allowed_domains=allowed_domains,
                    label=f"{key.title()} URL",
                )
            except Exception as exc:
                raise serializers.ValidationError({key: str(exc)}) from exc
        return cleaned

class EscrowSerializer(serializers.ModelSerializer):
    class Meta:
        model = Escrow
        fields = [
            'id', 'amount', 'status', 'mpesa_receipt', 'mpesa_release_receipt',
            'confirmation_code', 'created_at', 'released_at'
        ]

class MilestoneSerializer(serializers.ModelSerializer):
    class Meta:
        model = Milestone
        fields = ['id', 'title', 'description', 'amount', 'due_date', 'order', 'status', 'created_at']
        read_only_fields = ['id', 'status', 'created_at']

class ContractSerializer(serializers.ModelSerializer):
    escrow = EscrowSerializer(read_only=True)
    milestones = MilestoneSerializer(many=True, read_only=True)
    
    class Meta:
        model = Contract
        fields = ['id', 'project', 'contract_text', 'amount', 'status', 'payment_status', 
                  'client_signature', 'freelancer_signature', 'client_signed_at', 
                  'freelancer_signed_at', 'escrow', 'milestones', 'created_at', 'completed_at']
        read_only_fields = ['id', 'project', 'contract_text', 'amount', 'status', 'payment_status', 
                            'client_signed_at', 'freelancer_signed_at', 'created_at', 'completed_at']

class ProjectSerializer(serializers.ModelSerializer):
    client = UserSerializer(read_only=True)
    freelancer = UserSerializer(read_only=True)
    contract = ContractSerializer(read_only=True)
    
    # Adding escrow_status for legacy compatibility if frontend uses it directly from project
    escrow_status = serializers.SerializerMethodField()

    class Meta:
        model = Project
        fields = ['id', 'client', 'freelancer', 'title', 'description',
                 'scope_of_work', 'timeline', 'budget', 'payment_mode', 'milestone_plan',
                 'status', 'contract', 'escrow_status', 'created_at']
        read_only_fields = ['id', 'created_at', 'status']

    def get_escrow_status(self, obj):
        if hasattr(obj, 'contract') and hasattr(obj.contract, 'escrow'):
            return obj.contract.escrow.status
        return 'pending'

class ProjectCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Project
        fields = ['title', 'description', 'scope_of_work', 'timeline', 'budget', 'payment_mode', 'milestone_plan']
    
    def validate_budget(self, value):
        if value < 100:
            raise serializers.ValidationError("Minimum escrow amount is KSh 100.")
        return value

    def validate_payment_mode(self, value):
        return value or 'project_completion'

    def validate_milestone_plan(self, value):
        if value in (None, ''):
            return []
        if not isinstance(value, list):
            raise serializers.ValidationError("Milestones must be a list.")
        if len(value) > 12:
            raise serializers.ValidationError("Use 12 milestones or fewer.")

        cleaned = []
        for index, item in enumerate(value, start=1):
            if not isinstance(item, dict):
                raise serializers.ValidationError("Each milestone must be an object.")
            title = str(item.get('title') or '').strip()
            description = str(item.get('description') or '').strip()
            due_date = item.get('due_date') or None
            try:
                amount = Decimal(str(item.get('amount') or '0'))
            except Exception as exc:
                raise serializers.ValidationError(f"Milestone {index} amount is invalid.") from exc

            if not title:
                raise serializers.ValidationError(f"Milestone {index} needs a title.")
            if amount < Decimal('100'):
                raise serializers.ValidationError(f"Milestone {index} must be at least KSh 100.")

            cleaned.append({
                'title': title[:160],
                'description': description,
                'amount': str(amount),
                'due_date': due_date,
                'order': int(item.get('order') or index),
            })
        return cleaned

    def validate(self, attrs):
        payment_mode = attrs.get('payment_mode') or 'project_completion'
        milestone_plan = attrs.get('milestone_plan') or []

        if payment_mode == 'milestone':
            if not milestone_plan:
                raise serializers.ValidationError({'milestone_plan': 'Add at least one milestone.'})
            total = sum(Decimal(str(item['amount'])) for item in milestone_plan)
            budget = attrs.get('budget')
            if budget and total != budget:
                raise serializers.ValidationError({
                    'milestone_plan': 'Milestone amounts must add up to the total project budget.'
                })
        else:
            attrs['milestone_plan'] = []

        attrs['payment_mode'] = payment_mode
        return attrs

    def create(self, validated_data):
        request = self.context.get('request')
        validated_data['client'] = request.user
        return super().create(validated_data)

class ContractSignSerializer(serializers.Serializer):
    signature = serializers.CharField(max_length=255, required=True)

class EscrowDepositSerializer(serializers.Serializer):
    contract_id = serializers.UUIDField(required=True)
    # Phone number is fetched from profile logic in view, not passed here.

class DeliverableSerializer(serializers.ModelSerializer):
    class Meta:
        model = Deliverable
        fields = ['id', 'contract', 'file_paths', 'description', 
                  'submitted_at', 'status', 'approved', 'approved_at', 'rejection_reason']
        read_only_fields = ['id', 'contract', 'submitted_at', 'approved', 'approved_at']

    def to_representation(self, instance):
        ret = super().to_representation(instance)
        try:
            if instance.file_paths:
                import json
                data = json.loads(instance.file_paths)
                if isinstance(data, dict):
                    ret['submission_type'] = data.get('submission_type', 'file')
                    ret['file_url'] = data.get('file_url', '')
                    ret['content'] = data.get('content', '')
                elif isinstance(data, list) and data:
                    ret['submission_type'] = 'file'
                    ret['file_url'] = data[0]
        except Exception:
             pass
        return ret

class DeliverableCreateSerializer(serializers.ModelSerializer):
    files = serializers.ListField(
        child=serializers.FileField(max_length=100000, allow_empty_file=False, use_url=False),
        write_only=True,
        required=False
    )
    external_links = serializers.JSONField(required=False)

    class Meta:
        model = Deliverable
        fields = ['description', 'files', 'external_links']

class DisputeSerializer(serializers.ModelSerializer):
    raised_by = UserSerializer(read_only=True)

    class Meta:
        model = Dispute
        fields = ['id', 'project', 'raised_by', 'reason', 'evidence_url',
                'status', 'resolution', 'ai_recommendation', 'resolved_at',
                'created_at']
        read_only_fields = ['id', 'raised_by', 'status', 'resolved_at', 'created_at']

class DisputeCreateSerializer(serializers.ModelSerializer):
    project_id = serializers.UUIDField(write_only=True)
    evidence_url = serializers.CharField(required=False, allow_blank=True)
    evidence_file = serializers.CharField(required=False, allow_blank=True, write_only=True)

    class Meta:
        model = Dispute
        fields = ['project_id', 'reason', 'evidence_url', 'evidence_file']

    def validate_project_id(self, value):
        try:
            Project.objects.get(id=value)
            return value
        except Project.DoesNotExist:
            raise serializers.ValidationError("Project not found")

class ProposalSerializer(serializers.ModelSerializer):
    freelancer_name = serializers.CharField(source='freelancer.email', read_only=True)
    freelancer_readiness = serializers.SerializerMethodField()
    
    class Meta:
        model = Proposal
        fields = [
            'id', 'project', 'freelancer', 'freelancer_name', 'cover_letter',
            'bid_amount', 'relevant_experience', 'qualification_summary',
            'portfolio_url', 'verification_status', 'verification_score',
            'verification_breakdown', 'freelancer_readiness', 'status', 'created_at'
        ]
        read_only_fields = [
            'id', 'freelancer', 'verification_status', 'verification_score',
            'verification_breakdown', 'status', 'created_at'
        ]

    def validate_bid_amount(self, value):
        if value < 100:
            raise serializers.ValidationError("Minimum escrow amount is KSh 100.")
        return value

    def validate_portfolio_url(self, value):
        if not value:
            return value
        try:
            return validate_external_url(value, label="Portfolio URL")
        except Exception as exc:
            raise serializers.ValidationError(str(exc)) from exc

    def get_freelancer_readiness(self, obj):
        return calculate_freelancer_readiness(obj.freelancer)

    def validate(self, attrs):
        request = self.context.get('request')
        user = getattr(request, 'user', None)

        if user and user.user_type == 'freelancer':
            evaluation = evaluate_freelancer_for_project(attrs['project'], user, attrs)
            attrs['verification_status'] = evaluation['status']
            attrs['verification_score'] = evaluation['score']
            attrs['verification_breakdown'] = {
                **evaluation['breakdown'],
                'minimum_score': evaluation['minimum_score'],
                'advisory_only': True,
                'freelancer_readiness': calculate_freelancer_readiness(user),
            }

        return attrs

    def create(self, validated_data):
        user = self.context['request'].user
        validated_data['freelancer'] = user
        return super().create(validated_data)

class NotificationPreferenceSerializer(serializers.ModelSerializer):
    class Meta:
        model = NotificationPreference
        fields = ['email_notifications', 'project_updates', 'payment_notifications', 'dispute_alerts']

class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = ['id', 'notification_type', 'title', 'message', 'is_read', 'email_sent', 'created_at']
        read_only_fields = ['id', 'notification_type', 'title', 'message', 'email_sent', 'created_at']

class SkillAssessmentQuestionSerializer(serializers.ModelSerializer):
    class Meta:
        model = SkillAssessmentQuestion
        fields = ['id', 'skill', 'level', 'prompt', 'choices']

class SkillAssessmentAttemptSerializer(serializers.ModelSerializer):
    class Meta:
        model = SkillAssessmentAttempt
        fields = [
            'id', 'skill', 'level', 'current_index', 'score', 'correct_count',
            'total_questions', 'status', 'time_limit_seconds', 'started_at', 'completed_at'
        ]

class VerifiedSkillSerializer(serializers.ModelSerializer):
    skill_display = serializers.CharField(source='get_skill_display', read_only=True)
    level_display = serializers.CharField(source='get_level_display', read_only=True)

    class Meta:
        model = VerifiedSkill
        fields = [
            'skill', 'skill_display', 'level', 'level_display', 'best_score',
            'last_score', 'is_verified', 'verified_at', 'expires_at'
        ]
