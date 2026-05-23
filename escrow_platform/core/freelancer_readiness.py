from django.db.models import Avg, Q
from django.utils import timezone
from core.models import Dispute, Project, ProjectReview, VerifiedSkill


def _has_text(value):
    return bool(str(value or '').strip())


def _count_links(social_links):
    if not isinstance(social_links, dict):
        return 0
    return sum(1 for value in social_links.values() if _has_text(value))


def _level(score):
    if score >= 80:
        return 'trusted'
    if score >= 60:
        return 'ready'
    if score >= 40:
        return 'building'
    return 'needs_setup'


def calculate_freelancer_readiness(user):
    """
    A small-scale trust/readiness benchmark inspired by larger marketplaces.

    It intentionally uses data GigWay already has: profile completeness, contact
    details, verified proof links, proposals, completed work, and disputes.
    """
    if getattr(user, 'user_type', None) != 'freelancer':
        return None

    skills = user.skills if isinstance(user.skills, list) else []
    social_links = user.social_links if isinstance(user.social_links, dict) else {}

    profile_checks = {
        'bio': _has_text(user.bio),
        'profession': _has_text(user.profession),
        'skills': len(skills) >= 3,
        'location': _has_text(user.country) or _has_text(user.city),
        'profile_photo': bool(user.profile_picture),
    }
    profile_score = round((sum(profile_checks.values()) / len(profile_checks)) * 15)

    contact_checks = {
        'email': _has_text(user.email),
        'phone': _has_text(user.phone_number),
    }
    contact_score = round((sum(contact_checks.values()) / len(contact_checks)) * 15)

    proof_link_count = _count_links(social_links)
    proof_score = min(10, proof_link_count * 5)

    verified_skills = VerifiedSkill.objects.filter(
        user=user,
        is_verified=True,
    ).filter(Q(expires_at__isnull=True) | Q(expires_at__gt=timezone.now()))
    verified_skill_count = verified_skills.count()
    best_skill_score = verified_skills.order_by('-best_score').values_list('best_score', flat=True).first() or 0
    skill_verification_score = min(20, verified_skill_count * 8 + max(0, int(best_skill_score) - 70) // 3)

    assigned_projects = Project.objects.filter(freelancer=user)
    completed_count = assigned_projects.filter(status='completed').count()
    active_or_completed_count = assigned_projects.exclude(status='open').count()
    dispute_count = Dispute.objects.filter(project__freelancer=user).count()
    review_stats = ProjectReview.objects.filter(freelancer=user).aggregate(
        average_rating=Avg('rating')
    )
    review_count = ProjectReview.objects.filter(freelancer=user).count()
    average_rating = review_stats['average_rating'] or 0

    if completed_count >= 5:
        performance_score = 14
    elif completed_count >= 3:
        performance_score = 11
    elif completed_count >= 1:
        performance_score = 7
    elif active_or_completed_count >= 1:
        performance_score = 4
    else:
        performance_score = 0

    if review_count:
        performance_score += min(6, round((float(average_rating) / 5) * 6))
        if review_count >= 3 and average_rating >= 4:
            performance_score += 2

    performance_score = min(20, performance_score)
    performance_score = max(0, performance_score - min(10, dispute_count * 5))

    score = min(100, profile_score + contact_score + proof_score + skill_verification_score + performance_score)
    missing_actions = []
    if not profile_checks['profession']:
        missing_actions.append('Choose your profession.')
    if not profile_checks['skills']:
        missing_actions.append('Add at least 3 relevant skills.')
    if not profile_checks['bio']:
        missing_actions.append('Write a short bio that explains your experience.')
    if proof_link_count == 0:
        missing_actions.append('Add a verified GitHub, LinkedIn, or portfolio link.')
    if verified_skill_count == 0:
        missing_actions.append('Take an optional Lexa skill test to verify your strongest skill.')
    if completed_count == 0:
        missing_actions.append('Complete your first project to build performance history.')

    return {
        'score': score,
        'level': _level(score),
        'breakdown': {
            'profile_completeness': profile_score,
            'verified_contact': contact_score,
            'proof_links': proof_score,
            'skill_verification': skill_verification_score,
            'platform_performance': performance_score,
        },
        'stats': {
            'completed_projects': completed_count,
            'assigned_projects': active_or_completed_count,
            'disputes': dispute_count,
            'reviews': review_count,
            'average_rating': round(float(average_rating), 1) if average_rating else 0,
            'proof_links': proof_link_count,
            'verified_skills': verified_skill_count,
        },
        'next_actions': missing_actions[:4],
    }
