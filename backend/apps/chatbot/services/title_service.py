"""Smart conversation-title generation for the Afya Mkononi chat history.

`generate_conversation_title(text)` turns a user's first message into a short,
professional, ChatGPT-style label (2-5 words) such as "Headache Assessment" or
"Appointment Booking" — instead of a raw truncation of the message.

It works in three graceful tiers:

1. Keyword classification — fast, free, deterministic. Covers the common
   healthcare intents (symptoms, guidance, medication safety, appointments,
   reminders). This handles the large majority of real messages.
2. Optional lightweight AI call — only when classification can't confidently
   label the message (controlled by ``settings.CONVERSATION_TITLE_USE_AI``).
   All Anthropic SDK access stays inside ``ai_service``.
3. Fallback — a cleaned, shortened version of the first message, so a title is
   always produced even if every smarter step fails.
"""

from __future__ import annotations

import logging
import re

from django.conf import settings

logger = logging.getLogger(__name__)


# Canonical condition labels. Ordered so multi-word / more-specific phrases are
# matched before broader ones (e.g. "chest pain" before any generic match).
CONDITIONS: tuple[tuple[str, str], ...] = (
    ('chest pain', 'Chest Pain'),
    ('high blood pressure', 'Blood Pressure'),
    ('blood pressure', 'Blood Pressure'),
    ('hypertension', 'Blood Pressure'),
    ('sore throat', 'Sore Throat'),
    ('back pain', 'Back Pain'),
    ('stomach', 'Stomach Pain'),
    ('headache', 'Headache'),
    ('migraine', 'Migraine'),
    ('fever', 'Fever'),
    ('cough', 'Cough'),
    ('malaria', 'Malaria'),
    ('typhoid', 'Typhoid'),
    ('cholera', 'Cholera'),
    ('diabetes', 'Diabetes'),
    ('asthma', 'Asthma'),
    ('covid', 'COVID-19'),
    ('diarrhoea', 'Diarrhea'),
    ('diarrhea', 'Diarrhea'),
    ('vomiting', 'Vomiting'),
    ('nausea', 'Nausea'),
    ('toothache', 'Toothache'),
    ('rash', 'Skin Rash'),
    ('allergic', 'Allergy'),
    ('allergy', 'Allergy'),
    ('anxiety', 'Anxiety'),
    ('depression', 'Depression'),
    ('ulcer', 'Ulcers'),
    ('pregnan', 'Pregnancy'),
)

# Medicine names that signal a medication question.
MEDICATIONS: tuple[str, ...] = (
    'paracetamol', 'acetaminophen', 'panadol', 'ibuprofen', 'brufen',
    'aspirin', 'amoxicillin', 'antibiotic', 'antibiotics', 'metformin',
    'diclofenac', 'codeine', 'morphine', 'insulin', 'contraceptive',
    'antimalarial', 'antihistamine', 'painkiller', 'painkillers',
)

# Words that mark a cough (or similar) as ongoing -> "Persistent ...".
_PERSISTENCE_HINTS = (
    'week', 'weeks', 'day', 'days', 'month', 'persistent', 'still',
    'keeps', "won't stop", 'wont stop', 'two', 'three', 'several',
)

# Complaint cues: the user is describing something happening to them.
_COMPLAINT_RE = re.compile(
    r"\bi\s?('?ve| have| am| feel|m| had)\b|i've been|having|experiencing"
    r"|suffering|for \d+ (?:day|days|week|weeks|hour|hours|month|months)",
)
_INFO_RE = re.compile(
    r'symptoms? of|signs? of|what (?:is|are|causes)|tell me about|what does',
)
_GUIDANCE_RE = re.compile(
    r'\bhow (?:do|can|to|should)\b|\blower\b|\breduce\b|\bmanage\b'
    r'|\bprevent\b|\btreat\b|get rid of|deal with|\bimprove\b|\bcontrol\b',
)

# Complaint titles that read more naturally than "<Condition> Assessment".
_COMPLAINT_OVERRIDES = {
    'Fever': 'Fever Consultation',
}


def _has_medication(text: str) -> bool:
    return any(med in text for med in MEDICATIONS)


def _first_condition(text: str) -> str | None:
    """Return the canonical label of the first condition mentioned, if any."""
    for keyword, label in CONDITIONS:
        if keyword in text:
            return label
    return None


def _complaint_title(condition: str, text: str) -> str:
    if condition == 'Cough':
        if any(hint in text for hint in _PERSISTENCE_HINTS):
            return 'Persistent Cough'
        return 'Cough Assessment'
    if condition in _COMPLAINT_OVERRIDES:
        return _COMPLAINT_OVERRIDES[condition]
    return f'{condition} Assessment'


def _classify_title(text: str) -> str | None:
    """Keyword-based classification of common healthcare intents.

    Returns a polished title, or ``None`` when no rule confidently applies
    (so the caller can fall back to the AI or the raw message).
    """
    t = text.lower()

    # 1. Reminders ("remind me to take my medication" -> Medication Reminder).
    if re.search(r'\bremind(?:er)?\b', t):
        if (_has_medication(t) or 'medication' in t or 'medicine' in t
                or 'pill' in t or 'drug' in t or 'tablet' in t or 'take my' in t):
            return 'Medication Reminder'
        if 'appointment' in t:
            return 'Appointment Reminder'
        return 'Health Reminder'

    # 2. Appointments.
    if 'appointment' in t or re.search(r'\b(?:book|schedule|reschedule|cancel)\b', t):
        if 'cancel' in t:
            return 'Appointment Cancellation'
        if 'reschedul' in t:
            return 'Appointment Rescheduling'
        return 'Appointment Booking'

    # 3. Medication safety ("can I take paracetamol while pregnant?").
    if re.search(r'\bcan i take\b', t):
        return 'Medication Safety'
    if (_has_medication(t) or 'medication' in t or 'medicine' in t) and re.search(
        r'\bsafe\b|side effect|while pregnant|during pregnancy|interact|overdose', t,
    ):
        return 'Medication Safety'

    condition = _first_condition(t)

    # 4. Informational questions ("what are the symptoms of malaria?").
    if _INFO_RE.search(t):
        if condition:
            if 'what causes' in t or 'causes of' in t:
                return f'{condition} Guidance'
            return f'{condition} Information'
        return None

    # 5. Guidance / how-to ("how can I lower my blood pressure?").
    if _GUIDANCE_RE.search(t):
        if condition:
            return f'{condition} Guidance'
        return None

    # 6. Personal complaint ("I have a headache", "I've had a fever for 3 days").
    if condition and _COMPLAINT_RE.search(t):
        return _complaint_title(condition, t)

    # 7. Bare topic mention with nothing else to go on.
    if condition:
        return f'{condition} Information'

    return None


def _fallback_title(cleaned: str) -> str:
    """A cleaned, shortened version of the first message (last resort)."""
    sentence = re.split(r'[.!?\n]', cleaned, maxsplit=1)[0].strip() or cleaned
    words = sentence.split()
    truncated = ' '.join(words[:6])
    truncated_flag = len(words) > 6 or len(truncated) > 48
    if len(truncated) > 48:
        truncated = truncated[:48].rstrip()
    title = (truncated[:1].upper() + truncated[1:]) if truncated else cleaned
    if truncated_flag:
        title += '…'
    return title or 'New conversation'


def generate_conversation_title(text: str, *, use_ai: bool | None = None) -> str:
    """Produce a short, professional title for a conversation.

    ``text`` is the conversation's first user message. ``use_ai`` overrides the
    ``CONVERSATION_TITLE_USE_AI`` setting (handy for deterministic tests).
    Returns ``''`` only when ``text`` is empty.
    """
    cleaned = ' '.join((text or '').split())
    if not cleaned:
        return ''

    keyword_title = _classify_title(cleaned)
    if keyword_title:
        return keyword_title

    if use_ai is None:
        use_ai = getattr(settings, 'CONVERSATION_TITLE_USE_AI', True)
    if use_ai:
        try:
            from . import ai_service
            ai_title = ai_service.generate_title(cleaned)
        except Exception:
            logger.exception('AI title generation errored; using fallback')
            ai_title = None
        if ai_title:
            return ai_title

    return _fallback_title(cleaned)
