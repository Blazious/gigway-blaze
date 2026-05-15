"""
Notification Service for EscrowGig
Handles sending email notifications and creating notification records
"""
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
from core.models import Notification, NotificationPreference


def send_notification(recipient, notification_type, title, message, context=None):
    """
    Main function to send notifications
    """
    # Get or create user's notification preferences
    preferences, created = NotificationPreference.objects.get_or_create(
        user=recipient,
        defaults={
            'email_notifications': True,
            'project_updates': True,
            'payment_notifications': True,
            'dispute_alerts': True,
        }
    )
    
    # Check if user wants this type of notification
    should_send = preferences.email_notifications
    
    # Additional checks based on notification type
    if 'project' in notification_type or 'proposal' in notification_type:
        should_send = should_send and preferences.project_updates
    elif 'payment' in notification_type:
        should_send = should_send and preferences.payment_notifications
    elif 'dispute' in notification_type:
        should_send = should_send and preferences.dispute_alerts
    elif 'deliverable' in notification_type:
        should_send = should_send and preferences.project_updates
    
    # Create notification record
    notification = Notification.objects.create(
        recipient=recipient,
        notification_type=notification_type,
        title=title,
        message=message,
        is_read=False,
        email_sent=False
    )
    
    # Send email if preferences allow
    if should_send:
        try:
            email_subject = f"EscrowGig: {title}"
            email_body = f"""
Hello {recipient.email.split('@')[0].title()},

{message}

---
This is an automated notification from EscrowGig.
To manage your notification preferences, visit your Settings page.

Best regards,
The EscrowGig Team
            """
            
            send_mail(
                subject=email_subject,
                message=email_body,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[recipient.email],
                fail_silently=False,
            )
            
            notification.email_sent = True
            notification.save()
            
        except Exception as e:
            print(f"Failed to send email to {recipient.email}: {str(e)}")
    
    return notification


def send_project_notification(project, notification_type, recipient=None):
    """Send project-related notifications"""
    
    if notification_type == 'project_created':
        # Notify the client
        recipient = recipient or project.client
        title = "Project Created Successfully"
        message = f"Your project '{project.title}' has been created and is now open for proposals."
        
    elif notification_type == 'project_assigned':
        # Notify both client and freelancer
        if recipient == project.client:
            title = "Project Assigned"
            message = f"Your project '{project.title}' has been assigned to {project.freelancer.email}."
        else:
            recipient = project.freelancer
            title = "Project Assigned to You"
            message = f"Congratulations! You've been assigned to the project '{project.title}'."
            
    elif notification_type == 'project_completed':
        # Notify both parties
        if recipient == project.client:
            title = "Project Completed"
            message = f"The project '{project.title}' has been marked as completed."
        else:
            recipient = project.freelancer
            title = "Project Completed"
            message = f"The project '{project.title}' has been completed. Great work!"
            
    else:
        return None
    
    return send_notification(recipient, notification_type, title, message)


def send_proposal_notification(proposal, notification_type, recipient=None):
    """Send proposal-related notifications"""
    project = proposal.project
    
    if notification_type == 'proposal_received':
        # Notify client
        recipient = recipient or project.client
        title = "New Proposal Received"
        message = f"You have received a new proposal for your project '{project.title}' from {proposal.freelancer.email}."
        
    elif notification_type == 'proposal_accepted':
        # Notify freelancer
        recipient = recipient or proposal.freelancer
        title = "Proposal Accepted"
        message = f"Congratulations! Your proposal for the project '{project.title}' has been accepted."
        
    else:
        return None
    
    return send_notification(recipient, notification_type, title, message)


def send_payment_notification(escrow, notification_type, recipient=None):
    """Send payment-related notifications"""
    # Update: Escrow -> Contract -> Project
    project = escrow.contract.project
    
    if notification_type == 'payment_deposited':
        # Notify both client and freelancer
        if recipient == project.client:
            title = "Payment Deposited to Escrow"
            message = f"Your payment of KES {escrow.amount} for '{project.title}' has been successfully deposited to escrow."
        else:
            recipient = project.freelancer
            title = "Payment Received in Escrow"
            message = f"Payment of KES {escrow.amount} for '{project.title}' has been deposited to escrow and will be released upon project completion."
            
    elif notification_type == 'payment_released':
        # Notify both parties
        if recipient == project.client:
            title = "Payment Released"
            message = f"Payment of KES {escrow.amount} for '{project.title}' has been released to the freelancer."
        else:
            recipient = project.freelancer
            title = "Payment Received"
            message = f"Congratulations! You have received KES {escrow.amount} for completing '{project.title}'."
            
    else:
        return None
    
    return send_notification(recipient, notification_type, title, message)


def send_deliverable_notification(deliverable, notification_type, recipient=None):
    """Send deliverable-related notifications"""
    # Update: Deliverable -> Contract -> Project
    project = deliverable.contract.project
    
    if notification_type == 'deliverable_submitted':
        # Notify client
        recipient = recipient or project.client
        title = "New Deliverable Submitted"
        message = f"A deliverable has been submitted for your project '{project.title}'. Please review and approve or reject it."
        
    elif notification_type == 'deliverable_approved':
        # Notify freelancer
        recipient = recipient or deliverable.contract.freelancer
        title = "Deliverable Approved"
        message = f"Your deliverable for '{project.title}' has been approved by the client."
        
    elif notification_type == 'deliverable_rejected':
        # Notify freelancer
        recipient = recipient or deliverable.contract.freelancer
        title = "Deliverable Rejected"
        message = f"Your deliverable for '{project.title}' has been rejected. Reason: {deliverable.rejection_reason or 'No reason provided'}"
        
    else:
        return None
    
    return send_notification(recipient, notification_type, title, message)


def send_dispute_notification(dispute, notification_type, recipient=None):
    """Send dispute-related notifications"""
    project = dispute.project
    
    if notification_type == 'dispute_raised':
        # Notify the other party
        if dispute.raised_by == project.client:
            recipient = project.freelancer
            title = "Dispute Raised"
            message = f"A dispute has been raised by the client for project '{project.title}'. Our team will review it shortly."
        else:
            recipient = project.client
            title = "Dispute Raised"
            message = f"A dispute has been raised by the freelancer for project '{project.title}'. Our team will review it shortly."
            
    elif notification_type == 'dispute_resolved':
        # Notify both parties
        title = "Dispute Resolved"
        message = f"The dispute for project '{project.title}' has been resolved. Resolution: {dispute.resolution or 'See dispute details for more information.'}"
        
    else:
        return None
    
    return send_notification(recipient, notification_type, title, message)


def send_contract_notification(contract, notification_type, recipient):
    """Send contract-related notifications"""
    project = contract.project
    
    if notification_type == 'contract_signed':
        title = "Contract Signed"
        if contract.client_signature and contract.freelancer_signature:
            message = f"The contract for '{project.title}' has been fully signed by both parties. The project can now proceed."
        else:
            message = f"A party has signed the contract for '{project.title}'. Waiting for the other party to sign."
    else:
        return None
    
    return send_notification(recipient, notification_type, title, message)
