from datetime import datetime

def generate_contract_text(project):
    """
    Generate a professional freelance service agreement contract
    with dynamic project details
    """
    
    # Get current date
    contract_date = datetime.now().strftime('%B %d, %Y')
    
    # Client details
    client_name = project.client.email.split('@')[0].title()
    client_email = project.client.email
    client_phone = getattr(project.client, 'phone_number', 'Not provided')
    
    # Freelancer details
    if project.freelancer:
        freelancer_name = project.freelancer.email.split('@')[0].title()
        freelancer_email = project.freelancer.email
        freelancer_phone = getattr(project.freelancer, 'phone_number', 'Not provided')
    else:
        freelancer_name = '[To be assigned]'
        freelancer_email = '[To be assigned]'
        freelancer_phone = '[To be assigned]'
    
    # Project details
    project_title = project.title
    project_description = project.description
    scope_of_work = getattr(project, 'scope_of_work', 'As described in project details')
    budget = f"{float(project.budget):,.2f}"
    
    # Timeline
    if hasattr(project, 'timeline') and project.timeline:
        if isinstance(project.timeline, str):
            timeline = project.timeline
        else:
            timeline = project.timeline.strftime('%B %d, %Y')
    else:
        timeline = 'To be determined'
    
    # Generate contract text
    payment_mode = getattr(project, 'payment_mode', 'project_completion')
    milestone_plan = getattr(project, 'milestone_plan', []) or []
    if payment_mode == 'milestone' and milestone_plan:
        payment_method = 'M-Pesa Escrow System with milestone schedule'
        milestone_lines = []
        for item in milestone_plan:
            amount = float(item.get('amount') or 0)
            due_date = item.get('due_date') or 'Flexible'
            milestone_lines.append(
                f"   {item.get('order', len(milestone_lines) + 1)}. {item.get('title', 'Milestone')}: "
                f"KES {amount:,.2f} | Due: {due_date}"
            )
        payment_schedule = "\n".join(milestone_lines)
        escrow_deposit_terms = (
            "   The parties have selected a milestone payment schedule. The current platform payment rail "
            "secures the contract amount in escrow, while the milestone schedule defines review checkpoints "
            "and expected payment portions."
        )
    else:
        payment_method = 'M-Pesa Escrow System'
        payment_schedule = "   Single payment on project completion."
        escrow_deposit_terms = (
            f"   Upon signing this agreement, the Client shall deposit the full project "
            f"amount (KES {budget}) into the platform's secure escrow account via M-Pesa."
        )

    contract = f"""
═══════════════════════════════════════════════════════════════════════════
                        FREELANCE SERVICE AGREEMENT
═══════════════════════════════════════════════════════════════════════════

This Freelance Service Agreement ("Agreement") is entered into on {contract_date}

BETWEEN:

CLIENT:
    Name: {client_name}
    Email: {client_email}
    Phone: {client_phone}

AND

FREELANCER:
    Name: {freelancer_name}
    Email: {freelancer_email}
    Phone: {freelancer_phone}

═══════════════════════════════════════════════════════════════════════════
                              PROJECT DETAILS
═══════════════════════════════════════════════════════════════════════════

Project Title: {project_title}

Description:
{project_description}

Scope of Work:
{scope_of_work}

═══════════════════════════════════════════════════════════════════════════
                            FINANCIAL TERMS
═══════════════════════════════════════════════════════════════════════════

Total Project Budget: KES {budget}
Payment Method: {payment_method}
Project Timeline: {timeline}
Payment Schedule:
{payment_schedule}

═══════════════════════════════════════════════════════════════════════════
                            PAYMENT & ESCROW TERMS
═══════════════════════════════════════════════════════════════════════════

1. ESCROW DEPOSIT
{escrow_deposit_terms}

2. FUND HOLDING
   The escrow funds will be held securely by the platform and will not be 
   accessible to either party until the conditions for release are met.

3. WORK DELIVERY
   The Freelancer agrees to complete and deliver the project as described 
   in the Scope of Work by the agreed timeline: {timeline}

4. CLIENT REVIEW
   Upon submission of deliverables, the Client has seven (7) calendar days 
   to review the work and either:
   a) Approve the deliverables and authorize fund release, or
   b) Request reasonable revisions with specific feedback

5. FUND RELEASE
   Funds will be released to the Freelancer upon:
   a) Client's explicit approval of deliverables, or
   b) Expiration of 7-day review period without dispute

6. REVISIONS
   The Freelancer agrees to provide up to two (2) rounds of reasonable 
   revisions at no additional cost if requested within the review period.

═══════════════════════════════════════════════════════════════════════════
                            DISPUTE RESOLUTION
═══════════════════════════════════════════════════════════════════════════

1. If a dispute arises, either party may raise it through the platform's 
   dispute resolution system.

2. The platform will review evidence from both parties and make a binding 
   decision on fund distribution.

3. During dispute resolution, escrow funds remain frozen until resolution.

═══════════════════════════════════════════════════════════════════════════
                            GENERAL TERMS
═══════════════════════════════════════════════════════════════════════════

1. INTELLECTUAL PROPERTY
   Upon full payment, all work product and intellectual property rights 
   transfer to the Client.

2. CONFIDENTIALITY
   Both parties agree to maintain confidentiality of any sensitive 
   information shared during the project.

3. TERMINATION
   Either party may terminate this agreement with seven (7) days written 
   notice. In case of termination, payment will be prorated based on 
   work completed.

4. PLATFORM FEES
   The platform may charge service fees as per the published fee schedule.

5. GOVERNING LAW
   This agreement is governed by the laws of Kenya.

═══════════════════════════════════════════════════════════════════════════
                            SIGNATURES
═══════════════════════════════════════════════════════════════════════════

By signing below, both parties acknowledge that they have read, understood, 
and agree to be bound by the terms of this Agreement.


CLIENT SIGNATURE:
Signed: ________________________
Date: __________________________


FREELANCER SIGNATURE:
Signed: ________________________
Date: __________________________


═══════════════════════════════════════════════════════════════════════════
                    Contract generated via EscrowGig Platform
═══════════════════════════════════════════════════════════════════════════
    """
    
    return contract.strip()
