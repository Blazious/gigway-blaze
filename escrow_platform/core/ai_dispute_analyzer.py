import json
import logging
import os
import google.generativeai as genai
from dotenv import load_dotenv
from pathlib import Path
from .models import Project, Contract, Deliverable
from typing import Optional, Dict, List

logger = logging.getLogger(__name__)

# Initialize Gemini
load_dotenv(override=True)
genai.configure(api_key=os.getenv('GEMINI_API_KEY'))

_model = None

DEFAULT_GEMINI_MODEL = 'gemini-2.5-flash'
FALLBACK_GEMINI_MODELS = [
    DEFAULT_GEMINI_MODEL,
    'gemini-flash-latest',
    'gemini-2.0-flash',
]


def _normalize_model_name(model_name):
    return (model_name or DEFAULT_GEMINI_MODEL).replace('models/', '', 1)


def get_best_model():
    """Return configured Gemini model without doing slow network discovery at startup/request time."""
    model_name = _normalize_model_name(os.getenv('GEMINI_MODEL', DEFAULT_GEMINI_MODEL))
    return genai.GenerativeModel(model_name)

def get_model():
    global _model
    if _model is None:
        _model = get_best_model()
    return _model


def generate_content_with_fallback(prompt):
    """Generate content, retrying known-supported Gemini model names if the configured one is unavailable."""
    global _model

    configured_name = _normalize_model_name(os.getenv('GEMINI_MODEL', DEFAULT_GEMINI_MODEL))
    model_names = [configured_name] + [
        name for name in FALLBACK_GEMINI_MODELS
        if name != configured_name
    ]
    last_error = None

    for model_name in model_names:
        try:
            model = genai.GenerativeModel(model_name)
            logger.info("Lexa using Gemini model: %s", model_name)
            response = model.generate_content(prompt)
            _model = model
            return response
        except Exception as exc:
            last_error = exc
            logger.warning("Gemini model %s failed: %s", model_name, exc)

    raise last_error

# Knowledge base paths
KNOWLEDGE_BASE_DIR = Path(__file__).parent / 'knowledge_base'
EMPLOYMENT_LAW = KNOWLEDGE_BASE_DIR / 'kenyan_employment_law.md'
PLATFORM_POLICIES = KNOWLEDGE_BASE_DIR / 'platform_policies.md'
PAST_DISPUTES = KNOWLEDGE_BASE_DIR / 'past_disputes.json'

def load_knowledge_base():
    """Load all knowledge base files"""
    knowledge = {
        'law': '',
        'policies': '',
        'precedents': []
    }
    
    try:
        if EMPLOYMENT_LAW.exists():
            knowledge['law'] = EMPLOYMENT_LAW.read_text(encoding='utf-8')
            
        if PLATFORM_POLICIES.exists():
            knowledge['policies'] = PLATFORM_POLICIES.read_text(encoding='utf-8')
            
        if PAST_DISPUTES.exists():
            knowledge['precedents'] = json.loads(PAST_DISPUTES.read_text(encoding='utf-8'))
            
    except Exception as e:
        print(f"Error loading knowledge base: {e}")
        
    return knowledge


def _json_dumps_safe(value):
    return json.dumps(value, indent=2, default=str)


def _project_deliverables(project):
    contract = getattr(project, 'contract', None)
    if not contract:
        return Deliverable.objects.none()
    return contract.deliverables.all()


def _deliverable_payload(deliverable):
    payload = {}
    try:
        payload = json.loads(deliverable.file_paths or '{}')
    except (TypeError, ValueError):
        payload = {}

    return {
        'description': deliverable.description,
        'status': deliverable.status,
        'submitted_at': deliverable.submitted_at.isoformat() if deliverable.submitted_at else None,
        'submission_type': payload.get('submission_type'),
        'file_url': payload.get('file_url'),
        'content_excerpt': str(payload.get('content') or '')[:700],
        'rejection_reason': deliverable.rejection_reason,
    }


def build_project_dispute_context(project, dispute=None):
    contract = getattr(project, 'contract', None)
    deliverables = _project_deliverables(project)

    context = {
        'project': {
            'title': project.title,
            'description': project.description,
            'scope_of_work': project.scope_of_work,
            'budget': str(project.budget),
            'timeline': project.timeline.isoformat() if project.timeline else None,
            'status': project.status,
        },
        'contract': {
            'status': contract.status if contract else 'missing',
            'payment_status': contract.payment_status if contract else 'missing',
            'amount': str(contract.amount) if contract else None,
            'text': contract.contract_text if contract else 'No contract signed yet.',
        },
        'deliverables': [_deliverable_payload(item) for item in deliverables],
    }

    if dispute:
        context['dispute'] = {
            'reason': dispute.reason,
            'evidence': dispute.evidence_url,
            'status': dispute.status,
            'raised_by': dispute.raised_by.email if dispute.raised_by_id else None,
        }

    return context


def get_local_dispute_guidance(project_context, user_message=''):
    project = project_context.get('project', {})
    contract = project_context.get('contract', {})
    deliverables = project_context.get('deliverables', [])
    submitted = [item for item in deliverables if item.get('status') == 'submitted']
    rejected = [item for item in deliverables if item.get('status') == 'rejected']
    approved = [item for item in deliverables if item.get('status') == 'approved']

    checks = [
        f"Project: {project.get('title', 'selected project')}",
        f"Project status: {project.get('status', 'unknown')}",
        f"Payment status: {contract.get('payment_status', 'unknown')}",
        f"Deliverables found: {len(deliverables)}",
    ]

    if not deliverables:
        recommendation = (
            "I do not see any submitted deliverables yet. If the client is disputing non-delivery, "
            "ask the freelancer to submit the work or proof of work first. If the freelancer says work was done, "
            "they should attach a file, link, or clear text submission before funds are released."
        )
    elif approved:
        recommendation = (
            "At least one deliverable is already approved. If funds have not moved, check the escrow release status "
            "and confirmation code before opening a quality dispute."
        )
    elif rejected:
        recommendation = (
            "There is a rejected deliverable. Compare the rejection reason against the project scope and ask for a "
            "specific revision list. If the submitted work partially satisfies the scope, a partial release may be fair."
        )
    elif submitted:
        recommendation = (
            "There is a submitted deliverable awaiting review. The client should review it against the project scope, "
            "then either approve release or reject with a specific reason and evidence."
        )
    else:
        recommendation = (
            "The project has deliverable records, but none are in a clear submitted/approved/rejected state. "
            "Check the latest deliverable status and request supporting evidence from both sides."
        )

    return (
        "Here is my dispute-readiness analysis from the project record:\n\n"
        + "\n".join(f"- {item}" for item in checks)
        + "\n\nRecommended next step:\n"
        + recommendation
        + "\n\nFor a fair decision, keep the evidence tied to the contract scope, submitted deliverables, timestamps, and escrow status."
    )

def analyze_dispute_with_ai(dispute_id: str) -> Optional[Dict]:
    """
    Analyze dispute using AI with structured knowledge
    """
    from .models import Dispute # Import here to avoid circular import if any
    try:
        # Get dispute data from database
        dispute = Dispute.objects.get(id=dispute_id)
        project = dispute.project
        context = build_project_dispute_context(project, dispute)
        
        # Load knowledge base
        knowledge = load_knowledge_base()
        
        # Build the prompt
        prompt = f"""
        You are Lexa, the Lead Dispute Resolution AI for EscrowGig (Kenyan freelance platform).
        Analyze this dispute and provide a fair recommendation based on the project deliverables and contract.
        
        KNOWLEDGE BASE (Platform Rules & Laws):
        {_json_dumps_safe(knowledge)}
        
        CURRENT CASE CONTEXT:
        {_json_dumps_safe(context)}
        
        Your response must be a valid JSON object:
        {{
            "decision": "RELEASE_FULL" | "RELEASE_PARTIAL" | "REFUND",
            "percentage": 0-100,
            "legal_basis": "Cite relevant platform rules or laws",
            "reasoning": ["point1", "point2"],
            "summary": "Short explanation for the users",
            "confidence": "HIGH" | "MEDIUM" | "LOW"
        }}
        """
        
        # Call Gemini API
        response = generate_content_with_fallback(prompt)
        
        # Parse response
        try:
            # Clean response text in case Gemini adds markdown backticks
            response_text = response.text.strip()
            if response_text.startswith('```json'):
                response_text = response_text[7:-3].strip()
            elif response_text.startswith('```'):
                response_text = response_text[3:-3].strip()
                
            analysis = json.loads(response_text)
            return analysis
        except Exception as e:
            print(f"Failed to parse AI response: {e}")
            return None
            
    except Exception as e:
        print(f"Error during AI analysis: {e}")
        return None

def get_lexa_response(user_message: str, project_context: Optional[Dict] = None) -> str:
    """
    Get a general Q&A response from Lexa
    """
    knowledge = load_knowledge_base()
    
    context_str = ""
    if project_context:
        context_str = f"Specific Project Context:\n{_json_dumps_safe(project_context)}"
    
    prompt = f"""
    You are Lexa, the AI assistant for EscrowGig. You are professional, helpful, and firm about security.
    Help the user with their question. If they are asking about a specific project, use the provided context.
    
    KNOWLEDGE BASE:
    {_json_dumps_safe(knowledge)}
    
    {context_str}
    
    User Question: {user_message}
    
    Always maintain the persona of Lexa. Keep responses concise but helpful.
    """
    
    try:
        response = generate_content_with_fallback(prompt)
        return response.text.strip()
    except Exception as e:
        logger.exception("Lexa Gemini request failed")
        if project_context:
            return get_local_dispute_guidance(project_context, user_message)
        return (
            "I'm having trouble reaching the AI service right now, but I can still help with the basics: "
            "confirm the contract scope, check whether deliverables were submitted, compare any rejection notes "
            "against the agreed work, and keep escrow funds held until both sides provide evidence."
        )
