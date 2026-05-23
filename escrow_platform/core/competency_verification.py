import re

from core.link_verification import is_verified_external_url


MIN_VERIFICATION_SCORE = 55

SKILL_ALIASES = {
    'backend developer': {'backend', 'api', 'django', 'python', 'node', 'database'},
    'frontend developer': {'frontend', 'react', 'javascript', 'css', 'ui', 'web'},
    'fullstack developer': {'frontend', 'backend', 'react', 'api', 'database', 'web'},
    'mobile developer': {'mobile', 'android', 'ios', 'flutter', 'react native'},
    'ui/ux designer': {'ui', 'ux', 'figma', 'prototype', 'wireframe', 'design'},
    'devops engineer': {'devops', 'cloud', 'docker', 'ci', 'deployment', 'linux'},
    'data scientist': {'data', 'analytics', 'machine learning', 'python', 'modeling'},
    'content writer': {'writing', 'copywriting', 'seo', 'editing', 'content'},
}

STOPWORDS = {
    'and', 'the', 'for', 'with', 'that', 'this', 'from', 'into', 'will', 'have',
    'need', 'needs', 'able', 'your', 'you', 'are', 'our', 'project', 'work',
    'task', 'create', 'build', 'make', 'using', 'use', 'must', 'can', 'should',
}


def _tokens(value):
    text = str(value or '').lower()
    return {word for word in re.findall(r'[a-z0-9+#.]{2,}', text) if word not in STOPWORDS}


def _as_text(*values):
    return ' '.join(str(value or '') for value in values)


def _normalise_skills(skills):
    if not isinstance(skills, list):
        return set()
    return {str(skill).strip().lower() for skill in skills if str(skill).strip()}


def evaluate_freelancer_for_project(project, freelancer, proposal_data):
    project_text = _as_text(
        project.title,
        project.description,
        project.scope_of_work,
        ' '.join(project.required_skills or []),
        ' '.join(project.required_tools or []),
        project.experience_level,
        project.preferred_background,
    )
    project_tokens = _tokens(project_text)
    profile_text = _as_text(freelancer.profession, freelancer.bio)
    profile_tokens = _tokens(profile_text)
    freelancer_skills = _normalise_skills(freelancer.skills)
    skill_tokens = set()

    for skill in freelancer_skills:
        skill_tokens.update(_tokens(skill))

    profession = str(freelancer.profession or '').lower()
    profession_aliases = SKILL_ALIASES.get(profession, set())
    capability_tokens = profile_tokens | skill_tokens | profession_aliases
    matched_tokens = sorted(project_tokens & capability_tokens)
    skill_score = round(min(45, (len(matched_tokens) / max(len(project_tokens), 1)) * 90))

    profession_score = 0
    if profession:
        profession_words = _tokens(profession) | profession_aliases
        profession_score = 20 if project_tokens & profession_words else 8

    social_links = freelancer.social_links if isinstance(freelancer.social_links, dict) else {}
    has_portfolio = bool(proposal_data.get('portfolio_url'))
    if not has_portfolio:
        has_portfolio = (
            is_verified_external_url(social_links.get('portfolio'))
            or is_verified_external_url(social_links.get('github'), allowed_domains={'github.com'})
            or is_verified_external_url(social_links.get('linkedin'), allowed_domains={'linkedin.com'})
        )
    evidence_text = _as_text(proposal_data.get('relevant_experience'), proposal_data.get('qualification_summary'))
    evidence_score = 0
    if len(evidence_text.strip()) >= 80:
        evidence_score += 12
    elif len(evidence_text.strip()) >= 35:
        evidence_score += 7
    if has_portfolio:
        evidence_score += 8

    proposal_text = _as_text(
        proposal_data.get('cover_letter'),
        proposal_data.get('relevant_experience'),
        proposal_data.get('qualification_summary'),
    )
    proposal_matches = sorted(project_tokens & _tokens(proposal_text))
    proposal_score = round(min(15, (len(proposal_matches) / max(len(project_tokens), 1)) * 45))

    total = min(100, skill_score + profession_score + evidence_score + proposal_score)
    status = 'verified' if total >= MIN_VERIFICATION_SCORE else 'needs_review'

    return {
        'status': status,
        'score': total,
        'minimum_score': MIN_VERIFICATION_SCORE,
        'breakdown': {
            'skill_match': skill_score,
            'profession_fit': profession_score,
            'qualification_evidence': evidence_score,
            'proposal_specificity': proposal_score,
            'matched_requirements': matched_tokens[:12],
            'proposal_requirement_matches': proposal_matches[:12],
        }
    }
