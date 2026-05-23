import json
import logging

from core.ai_dispute_analyzer import generate_content_with_fallback

logger = logging.getLogger(__name__)


def _json_dumps(value):
    return json.dumps(value, default=str, ensure_ascii=False, indent=2)


def _parse_gemini_json(text):
    response_text = str(text or '').strip()
    if response_text.startswith('```json'):
        response_text = response_text[7:].strip()
    if response_text.startswith('```'):
        response_text = response_text[3:].strip()
    if response_text.endswith('```'):
        response_text = response_text[:-3].strip()
    return json.loads(response_text)


def _work_history_payload(entries):
    return [
        {
            'job_title': item.job_title,
            'company': item.company,
            'start_date': item.start_date.isoformat() if item.start_date else None,
            'end_date': item.end_date.isoformat() if item.end_date else None,
            'description': item.description,
            'skills_used': item.skills_used if isinstance(item.skills_used, list) else [],
        }
        for item in entries
    ]


def generate_proposal_prefill(project, freelancer, work_history):
    history = _work_history_payload(work_history)
    if not history:
        raise ValueError('Add at least one work history entry before using AI proposal drafting.')

    project_payload = {
        'title': project.title,
        'description': project.description,
        'scope_of_work': project.scope_of_work,
        'budget': str(project.budget),
        'timeline': project.timeline.isoformat() if project.timeline else None,
        'required_skills': project.required_skills if isinstance(project.required_skills, list) else [],
        'required_tools': project.required_tools if isinstance(project.required_tools, list) else [],
        'experience_level': project.experience_level,
        'preferred_background': project.preferred_background,
    }
    freelancer_payload = {
        'profession': freelancer.profession,
        'bio': freelancer.bio,
        'skills': freelancer.skills if isinstance(freelancer.skills, list) else [],
        'work_history': history,
    }

    prompt = f"""
You help freelancers on GigWay draft honest, specific project proposals.

Use ONLY the freelancer profile and saved work history below. Do not invent employers,
projects, years of experience, tools, results, certifications, or claims. If the
work history does not prove something, phrase it cautiously or omit it.

PROJECT:
{_json_dumps(project_payload)}

FREELANCER:
{_json_dumps(freelancer_payload)}

Return ONLY a valid JSON object with these keys:
{{
  "cover_letter": "150-200 words, professional, specific to the project, editable by freelancer",
  "relevant_experience": "2-4 sentences grounded in saved work history",
  "qualification_summary": "1-3 sentences about matching skills/tools/strengths",
  "matched_skills": ["skills/tools that appear in both project needs and freelancer history/profile"],
  "most_relevant_role": "job title + company, or empty string if no clear match"
}}
"""

    response = generate_content_with_fallback(prompt)
    result = _parse_gemini_json(response.text)
    return {
        'cover_letter': str(result.get('cover_letter') or '').strip(),
        'relevant_experience': str(result.get('relevant_experience') or '').strip(),
        'qualification_summary': str(result.get('qualification_summary') or '').strip(),
        'matched_skills': [
            str(item).strip()[:60]
            for item in result.get('matched_skills') or []
            if str(item).strip()
        ][:20],
        'most_relevant_role': str(result.get('most_relevant_role') or '').strip()[:260],
    }
