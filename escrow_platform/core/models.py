import uuid
from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.utils.translation import gettext_lazy as _
from django.utils import timezone

class CustomUserManager(BaseUserManager):
    def create_user(self, email, password, phone_number, user_type, **extra_fields):
        if not email:
            raise ValueError(_('The Email must be set'))
        if not phone_number:
            raise ValueError(_('The Phone Number must be set'))
        if not user_type:
            raise ValueError(_('User Type must be specified'))
        
        email = self.normalize_email(email)
        user = self.model(
            email=email,
            phone_number=phone_number,
            user_type=user_type,
            **extra_fields
        )
        user.set_password(password)
        user.save()
        return user

    def create_superuser(self, email, password, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)
        
        if extra_fields.get('is_staff') is not True:
            raise ValueError(_('Superuser must have is_staff=True.'))
        if extra_fields.get('is_superuser') is not True:
            raise ValueError(_('Superuser must have is_superuser=True.'))
        
        return self.create_user(
            email=email,
            password=password,
            phone_number='+1234567890',  # Default phone for superuser
            user_type='freelancer',       # Default type for superuser
            **extra_fields
        )

class CustomUser(AbstractBaseUser, PermissionsMixin):
    USER_TYPE_CHOICES = [
        ('client', 'Client'),
        ('freelancer', 'Freelancer'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(_('email address'), unique=True)
    phone_number = models.CharField(_('phone number'), max_length=15)
    user_type = models.CharField(_('user type'), max_length=10, choices=USER_TYPE_CHOICES)
    bio = models.TextField(_('bio'), blank=True, null=True)
    profile_picture = models.ImageField(_('profile picture'), upload_to='profile_pics/', blank=True, null=True)
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    is_active = models.BooleanField(_('is active'), default=True)
    is_staff = models.BooleanField(_('is staff'), default=False)
    
    # Extended Profile Fields
    profession = models.CharField(_('profession/industry'), max_length=100, blank=True, null=True)
    skills = models.JSONField(_('skills'), default=list, blank=True)
    social_links = models.JSONField(_('social links'), default=dict, blank=True)
    country = models.CharField(_('country'), max_length=100, blank=True, null=True)
    city = models.CharField(_('city'), max_length=100, blank=True, null=True)
    company_name = models.CharField(_('company name'), max_length=200, blank=True, null=True)

    objects = CustomUserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    def __str__(self):
        return self.email

class Project(models.Model):
    STATUS_CHOICES = [
        ('open', 'Open'),
        ('assigned', 'Assigned'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('disputed', 'Disputed'),
    ]
    PAYMENT_MODE_CHOICES = [
        ('project_completion', 'Pay at Project Completion'),
        ('milestone', 'Pay by Milestone'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    client = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='projects_created'
    )
    freelancer = models.ForeignKey(
        CustomUser,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='projects_assigned'
    )
    title = models.CharField(max_length=200)
    description = models.TextField()
    scope_of_work = models.TextField()
    timeline = models.DateField()
    budget = models.DecimalField(max_digits=10, decimal_places=2)
    required_skills = models.JSONField(default=list, blank=True)
    required_tools = models.JSONField(default=list, blank=True)
    experience_level = models.CharField(max_length=30, blank=True)
    preferred_background = models.TextField(blank=True)
    payment_mode = models.CharField(
        max_length=24,
        choices=PAYMENT_MODE_CHOICES,
        default='project_completion'
    )
    milestone_plan = models.JSONField(default=list, blank=True)
    status = models.CharField(
        max_length=11,
        choices=STATUS_CHOICES,
        default='open'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.title} - {self.get_status_display()}"

    class Meta:
        ordering = ['-created_at']

class WorkHistory(models.Model):
    SOURCE_CHOICES = [
        ('manual', 'Manual'),
        ('profile', 'Profile'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    freelancer = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='work_history'
    )
    job_title = models.CharField(max_length=200)
    company = models.CharField(max_length=200, blank=True)
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    description = models.TextField()
    skills_used = models.JSONField(default=list, blank=True)
    source = models.CharField(max_length=30, choices=SOURCE_CHOICES, default='manual')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        company = f" at {self.company}" if self.company else ""
        return f"{self.job_title}{company}"

    class Meta:
        ordering = ['-start_date', '-created_at']

class Proposal(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('accepted', 'Accepted'),
        ('rejected', 'Rejected'),
    ]
    VERIFICATION_STATUS_CHOICES = [
        ('verified', 'Verified'),
        ('needs_review', 'Needs Review'),
        ('rejected', 'Rejected'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name='proposals'
    )
    freelancer = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='proposals'
    )
    cover_letter = models.TextField()
    bid_amount = models.DecimalField(max_digits=10, decimal_places=2)
    relevant_experience = models.TextField(blank=True)
    qualification_summary = models.TextField(blank=True)
    portfolio_url = models.URLField(max_length=500, blank=True)
    ai_matched_skills = models.JSONField(default=list, blank=True)
    ai_most_relevant_role = models.CharField(max_length=260, blank=True)
    verification_status = models.CharField(
        max_length=20,
        choices=VERIFICATION_STATUS_CHOICES,
        default='needs_review'
    )
    verification_score = models.PositiveSmallIntegerField(default=0)
    verification_breakdown = models.JSONField(default=dict, blank=True)
    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default='pending'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Proposal for {self.project.title} by {self.freelancer.email}"

    class Meta:
        ordering = ['-created_at']
        unique_together = ['project', 'freelancer']

class Contract(models.Model):
    STATUS_CHOICES = [
        ('pending_signature', 'Pending Signature'),
        ('signed', 'Signed'),
        ('deliverables_submitted', 'Deliverables Submitted'),
        ('completed', 'Completed'),
    ]
    
    PAYMENT_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('escrowed', 'Funds in Escrow'),
        ('released', 'Funds Released'),
        ('refunded', 'Funds Refunded'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    project = models.OneToOneField(
        Project,
        on_delete=models.CASCADE,
        related_name='contract'
    )
    freelancer = models.ForeignKey(
        CustomUser, 
        on_delete=models.CASCADE, 
        related_name='freelancer_contracts',
        null=True, blank=True
    )
    client = models.ForeignKey(
        CustomUser, 
        on_delete=models.CASCADE, 
        related_name='client_contracts',
        null=True, blank=True
    )
    
    contract_text = models.TextField()
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    
    status = models.CharField(
        max_length=30,
        choices=STATUS_CHOICES,
        default='pending_signature'
    )
    payment_status = models.CharField(
        max_length=20,
        choices=PAYMENT_STATUS_CHOICES,
        default='pending'
    )
    
    client_signature = models.CharField(max_length=255, null=True, blank=True)
    freelancer_signature = models.CharField(max_length=255, null=True, blank=True)
    client_signed_at = models.DateTimeField(null=True, blank=True)
    freelancer_signed_at = models.DateTimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Contract for {self.project.title} - {self.get_status_display()}"

    class Meta:
        ordering = ['-created_at']

class Escrow(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('held', 'Funds Held'),
        ('released', 'Funds Released'),
        ('releasing', 'Processing Release'),
        ('failed', 'Transaction Failed'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    contract = models.OneToOneField(
        Contract,
        on_delete=models.CASCADE,
        related_name='escrow'
    )
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending'
    )
    
    mpesa_receipt = models.CharField(max_length=100, null=True, blank=True) # Deposit receipt
    mpesa_release_receipt = models.CharField(max_length=100, null=True, blank=True) # Release receipt
    confirmation_code = models.CharField(max_length=100, null=True, blank=True)
    mpesa_checkout_request_id = models.CharField(max_length=100, null=True, blank=True)
    mpesa_conversation_id = models.CharField(max_length=100, null=True, blank=True) # Check for B2C
    
    created_at = models.DateTimeField(auto_now_add=True)
    released_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Escrow #{self.id} for Contract {self.contract.id}"

    class Meta:
        ordering = ['-created_at']
        verbose_name_plural = "Escrow"

class Milestone(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('funded', 'Funded'),
        ('submitted', 'Submitted'),
        ('approved', 'Approved'),
        ('released', 'Released'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    contract = models.ForeignKey(
        Contract,
        on_delete=models.CASCADE,
        related_name='milestones'
    )
    title = models.CharField(max_length=160)
    description = models.TextField(blank=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    due_date = models.DateField(null=True, blank=True)
    order = models.PositiveIntegerField(default=1)
    status = models.CharField(
        max_length=12,
        choices=STATUS_CHOICES,
        default='pending'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['order', 'created_at']

    def __str__(self):
        return f"{self.title} - {self.contract.project.title}"

class Deliverable(models.Model):
    STATUS_CHOICES = [
        ('submitted', 'Submitted'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    contract = models.ForeignKey(
        Contract,
        on_delete=models.CASCADE,
        related_name='deliverables'
    )
    file_paths = models.TextField(null=True, blank=True) # JSON or comma-separated list of file paths
    description = models.TextField()
    submitted_at = models.DateTimeField(auto_now_add=True)
    
    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default='submitted'
    )
    approved = models.BooleanField(default=False)
    approved_at = models.DateTimeField(null=True, blank=True)
    
    rejection_reason = models.TextField(null=True, blank=True)

    def __str__(self):
        return f"Deliverable for {self.contract.project.title} - {self.get_status_display()}"

    class Meta:
        ordering = ['-submitted_at']

class Dispute(models.Model):
    STATUS_CHOICES = [
        ('open', 'Open'),
        ('under_review', 'Under Review'),
        ('resolved', 'Resolved'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name='disputes'
    )
    raised_by = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='disputes_raised'
    )
    reason = models.TextField()
    evidence_url = models.CharField(max_length=500, null=True, blank=True)
    status = models.CharField(
        max_length=12,
        choices=STATUS_CHOICES,
        default='open'
    )
    resolution = models.TextField(null=True, blank=True)
    ai_recommendation = models.JSONField(null=True, blank=True)
    resolved_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Dispute for {self.project.title} by {self.raised_by.email}"

    class Meta:
        ordering = ['-created_at']

class NotificationPreference(models.Model):
    """Stores user notification preferences"""
    user = models.OneToOneField(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='notification_preferences'
    )
    email_notifications = models.BooleanField(default=True)
    project_updates = models.BooleanField(default=True)
    payment_notifications = models.BooleanField(default=True)
    dispute_alerts = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Notification Preferences for {self.user.email}"

    class Meta:
        verbose_name_plural = "Notification Preferences"

class Notification(models.Model):
    """Stores notification history"""
    NOTIFICATION_TYPES = [
        ('project_created', 'Project Created'),
        ('project_assigned', 'Project Assigned'),
        ('project_completed', 'Project Completed'),
        ('proposal_received', 'Proposal Received'),
        ('proposal_accepted', 'Proposal Accepted'),
        ('payment_deposited', 'Payment Deposited'),
        ('payment_released', 'Payment Released'),
        ('deliverable_submitted', 'Deliverable Submitted'),
        ('deliverable_approved', 'Deliverable Approved'),
        ('deliverable_rejected', 'Deliverable Rejected'),
        ('dispute_raised', 'Dispute Raised'),
        ('dispute_resolved', 'Dispute Resolved'),
        ('contract_signed', 'Contract Signed'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    recipient = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='notifications'
    )
    notification_type = models.CharField(max_length=30, choices=NOTIFICATION_TYPES)
    title = models.CharField(max_length=200)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    email_sent = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.title} - {self.recipient.email}"

    class Meta:
        ordering = ['-created_at']

class SkillAssessmentQuestion(models.Model):
    SKILL_CHOICES = [
        ('web_development', 'Web Development'),
        ('design', 'Design'),
        ('writing', 'Writing'),
    ]
    LEVEL_CHOICES = [
        ('beginner', 'Beginner'),
        ('intermediate', 'Intermediate'),
        ('advanced', 'Advanced'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    skill = models.CharField(max_length=40, choices=SKILL_CHOICES)
    level = models.CharField(max_length=20, choices=LEVEL_CHOICES)
    prompt = models.TextField()
    choices = models.JSONField(default=list)
    correct_choice = models.CharField(max_length=5)
    explanation = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['skill', 'level', 'created_at']

    def __str__(self):
        return f"{self.get_skill_display()} {self.get_level_display()}: {self.prompt[:50]}"

class SkillAssessmentAttempt(models.Model):
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('completed', 'Completed'),
        ('expired', 'Expired'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='skill_assessment_attempts'
    )
    skill = models.CharField(max_length=40, choices=SkillAssessmentQuestion.SKILL_CHOICES)
    level = models.CharField(max_length=20, choices=SkillAssessmentQuestion.LEVEL_CHOICES)
    question_ids = models.JSONField(default=list)
    current_index = models.PositiveIntegerField(default=0)
    score = models.PositiveSmallIntegerField(default=0)
    correct_count = models.PositiveSmallIntegerField(default=0)
    total_questions = models.PositiveSmallIntegerField(default=0)
    status = models.CharField(max_length=12, choices=STATUS_CHOICES, default='active')
    question_started_at = models.DateTimeField(default=timezone.now)
    time_limit_seconds = models.PositiveSmallIntegerField(default=120)
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-started_at']

    def __str__(self):
        return f"{self.user.email} - {self.skill} ({self.status})"

class SkillAssessmentAnswer(models.Model):
    attempt = models.ForeignKey(
        SkillAssessmentAttempt,
        on_delete=models.CASCADE,
        related_name='answers'
    )
    question = models.ForeignKey(SkillAssessmentQuestion, on_delete=models.CASCADE)
    selected_choice = models.CharField(max_length=5, blank=True)
    is_correct = models.BooleanField(default=False)
    timed_out = models.BooleanField(default=False)
    answered_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['answered_at']
        unique_together = ['attempt', 'question']

class VerifiedSkill(models.Model):
    user = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='verified_skills'
    )
    skill = models.CharField(max_length=40, choices=SkillAssessmentQuestion.SKILL_CHOICES)
    level = models.CharField(max_length=20, choices=SkillAssessmentQuestion.LEVEL_CHOICES)
    best_score = models.PositiveSmallIntegerField(default=0)
    last_score = models.PositiveSmallIntegerField(default=0)
    is_verified = models.BooleanField(default=False)
    verified_at = models.DateTimeField(null=True, blank=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['user', 'skill', 'level']
        ordering = ['skill', 'level']

    def __str__(self):
        return f"{self.user.email} - {self.skill} {self.best_score}%"
