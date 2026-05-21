from datetime import datetime, timezone
from django.utils import timezone as django_timezone

def analyze_dispute_simple(dispute):
    """Rule-based analysis of dispute to recommend resolution"""
    project = dispute.project
    contract = getattr(project, 'contract', None)
    deliverables = contract.deliverables.all() if contract else []
    
    # Default analysis result
    analysis = {
        "decision": "REFUND",
        "percentage": 0,
        "reasoning": [],
        "confidence": "MEDIUM"
    }

    # Rule 1: Check if deliverable was submitted
    if not contract or not deliverables.exists():
        analysis["reasoning"].append("No deliverables submitted")
        return analysis

    latest_deliverable = deliverables.latest('submitted_at')
    
    # Rule 2: Check submission timeliness
    # Convert timezone aware datetime to date for comparison with DateField
    submission_date = latest_deliverable.submitted_at.date()
    is_late = submission_date > contract.project.timeline
    
    if is_late:
        days_late = (submission_date - contract.project.timeline).days
        analysis["reasoning"].append(f"Delivered {days_late} days late")
    
    # Rule 3: Format approval (simplified check)
    accepted_formats = ['.pdf', '.doc', '.docx', '.zip']
    file_paths = latest_deliverable.file_paths or ''
    has_correct_format = any(fmt in file_paths.lower() for fmt in accepted_formats)
    
    # Decision logic
    if not is_late and has_correct_format:
        analysis.update({
            "decision": "RELEASE_FULL",
            "percentage": 100,
            "reasoning": ["On-time delivery", "Correct format"],
            "confidence": "HIGH"
        })
    elif is_late and has_correct_format:
        analysis.update({
            "decision": "RELEASE_PARTIAL",
            "percentage": 80,
            "reasoning": ["Late delivery", "Correct format"],
            "confidence": "MEDIUM"
        })
    elif not has_correct_format:
        analysis.update({
            "decision": "RELEASE_PARTIAL",
            "percentage": 50,
            "reasoning": ["Incorrect format files"],
            "confidence": "MEDIUM"
        })

    return analysis
