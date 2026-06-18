"""Anthropic Claude integration for the Afya Mkononi chatbot.

All Anthropic SDK usage is isolated to this module. Views call
`generate_reply(conversation, user_message)` and receive a (reply,
safety_category) tuple; they never import `anthropic` directly.
"""

from __future__ import annotations

import logging
from typing import Tuple

import anthropic
from django.conf import settings

from ..models import Conversation, Message

logger = logging.getLogger(__name__)


SYSTEM_PROMPT = """You are Afya Mkononi, a Kenyan healthcare informational assistant.

ROLE
- Provide general health information, education, and supportive guidance.
- Help users understand symptoms, healthy habits, and when to seek professional care.
- Use a warm, clear, concise tone. Plain language. Short paragraphs.

ABSOLUTE BOUNDARIES — never cross these:
- Do NOT diagnose. You may describe what symptoms can sometimes be associated with, but never tell a user what they have.
- Do NOT prescribe medication, doses, or specific treatment regimens.
- Do NOT give emergency treatment instructions beyond "call emergency services / go to the nearest hospital now".
- Do NOT replace a clinician. Always encourage the user to consult a qualified healthcare provider for diagnosis, prescriptions, and treatment decisions.

EMERGENCY HANDLING
If the user describes signs of a medical emergency (chest pain, difficulty breathing, severe bleeding, stroke signs, suicidal intent, loss of consciousness, severe allergic reaction, signs of labour complications, or similar), your reply MUST:
1. Tell them clearly this may be an emergency.
2. Instruct them to call Kenya emergency services (999 / 112) or go to the nearest hospital immediately.
3. Keep the message short and direct. Do not give home treatment steps.

IMAGES AND DOCUMENTS
Users may share an image (e.g. a photo of a skin area, a rash, or a document) or
a text document (PDF/DOCX/TXT, e.g. a lab report or discharge summary).
- Images are for EDUCATIONAL GUIDANCE ONLY. Do NOT diagnose diseases or
  conditions from an image. You may describe, in general terms, what is visible
  and what such appearances can sometimes be associated with — never a verdict.
- If an image suggests a potentially serious condition, clearly recommend
  evaluation by a qualified healthcare professional.
- For documents, you may summarise or explain the content in plain language and
  help the user understand terminology, while still never diagnosing or
  prescribing. Remind the user to discuss results with their clinician.
- If an image is unclear or you cannot tell what it shows, say so plainly.

STYLE
- 2-4 short paragraphs is usually enough.
- If a question is outside healthcare, briefly redirect to health-related help.
- End informational answers with a gentle nudge to consult a healthcare professional when relevant.
"""

FALLBACK_REPLY = (
    "I'm having trouble reaching my assistant right now. Please try again in a moment. "
    "If this is a medical emergency, call 999 or 112, or go to the nearest hospital immediately."
)

TITLE_SYSTEM_PROMPT = """You name healthcare chat conversations.

Given a user's first message, reply with a SHORT, professional title for the
conversation — the kind that belongs in a healthcare app's history sidebar.

RULES:
- 2 to 5 words. Title Case.
- Describe the topic, not the user. No first person, no questions, no quotes.
- No diagnosis and no punctuation at the end.
- Examples: "Headache Assessment", "Appointment Booking", "Medication Safety",
  "Blood Pressure Guidance", "Malaria Information".

Reply with ONLY the title text. Nothing else."""

EMERGENCY_KEYWORDS = (
    'chest pain', 'cannot breathe', "can't breathe", 'difficulty breathing',
    'severe bleeding', 'unconscious', 'suicide', 'kill myself', 'overdose',
    'stroke', 'heart attack', 'choking', 'severe allergic',
)


def _classify_safety(user_message: str, ai_reply: str) -> str:
    """Best-effort safety tag for the persisted Message.

    Keyword-based — intentionally simple. The real guardrails live in the
    system prompt; this just labels rows so the team can audit later.
    """
    haystack = f"{user_message}\n{ai_reply}".lower()
    if any(kw in haystack for kw in EMERGENCY_KEYWORDS):
        return Message.SafetyCategory.EMERGENCY
    return Message.SafetyCategory.NORMAL


def _build_history(conversation: Conversation, limit: int) -> list[dict]:
    """Pull recent USER/AI turns from the conversation as Anthropic message dicts.

    SYSTEM-sender rows are skipped — system context lives in the system prompt,
    not the message history.
    """
    qs = (
        conversation.messages
        .filter(sender_type__in=[Message.SenderType.USER, Message.SenderType.AI])
        .order_by('-created_at')[:limit]
    )
    recent = list(reversed(list(qs)))

    role_map = {
        Message.SenderType.USER: 'user',
        Message.SenderType.AI: 'assistant',
    }
    messages = []
    for msg in recent:
        # History is text-only: prior images/documents are summarised as a short
        # note rather than re-uploaded every turn (cost + the Anthropic API
        # rejects empty content for attachment-only turns).
        content = msg.message_content
        if not content:
            names = [a.name for a in msg.attachments.all()]
            if names:
                content = f"(The user previously shared: {', '.join(names)}.)"
        if not content:
            continue
        messages.append({
            'role': role_map[msg.sender_type],
            'content': content,
        })
    return messages


def _build_user_content(user_message: str, attachment):
    """Build the Anthropic ``content`` for the current user turn.

    * No attachment -> plain string.
    * Image -> list of [image block, text block] (Anthropic vision).
    * Document -> string with the extracted text folded in.

    Returns a string or a list of content blocks.
    """
    if attachment is None:
        return user_message

    # Local import keeps the Anthropic module free of Django/storage concerns.
    from . import attachments as attachment_service

    if attachment.is_image:
        payload = attachment_service.image_payload(attachment)
        if payload is None:
            # Could not read the image — fall back to a text-only note.
            note = f"(The user tried to share an image named '{attachment.name}' but it could not be read.)"
            return f"{user_message}\n\n{note}" if user_message else note
        text = user_message.strip() or (
            "I'm sharing an image. Please give general, educational health "
            "information about what it may show. Do not diagnose."
        )
        return [
            {
                'type': 'image',
                'source': {
                    'type': 'base64',
                    'media_type': payload['media_type'],
                    'data': payload['data'],
                },
            },
            {'type': 'text', 'text': text},
        ]

    # Document: fold extracted text into the prompt.
    extracted = attachment.extracted_text or ''
    if extracted:
        doc_block = (
            f"The user shared a document named '{attachment.name}'. "
            f"Here is its extracted text:\n\n\"\"\"\n{extracted}\n\"\"\""
        )
    else:
        doc_block = (
            f"The user shared a document named '{attachment.name}', but no text "
            f"could be extracted from it."
        )
    return f"{user_message}\n\n{doc_block}" if user_message.strip() else doc_block


def generate_reply(conversation: Conversation, user_message: str, attachment=None) -> Tuple[str, str]:
    """Generate a Claude reply for the given conversation and new user message.

    ``attachment`` is an optional ``ChatAttachment`` for the current turn: images
    are sent as Anthropic vision input, documents have their extracted text
    folded into the prompt. Returns (reply_text, safety_category). On any API
    failure returns a safe fallback so the chat flow never breaks.

    The caller persists both the user message (before this call) and the
    returned AI message — ai_service.py does not touch the database.
    """
    api_key = settings.ANTHROPIC_API_KEY
    if not api_key:
        logger.error('ANTHROPIC_API_KEY is empty; falling back.')
        return FALLBACK_REPLY, Message.SafetyCategory.NORMAL

    history = _build_history(conversation, settings.ANTHROPIC_HISTORY_TURNS)
    history.append({'role': 'user', 'content': _build_user_content(user_message, attachment)})

    try:
        client = anthropic.Anthropic(api_key=api_key)
        response = client.messages.create(
            model=settings.ANTHROPIC_MODEL,
            max_tokens=settings.ANTHROPIC_MAX_TOKENS,
            system=SYSTEM_PROMPT,
            messages=history,
        )
    except anthropic.APIStatusError as exc:
        logger.exception('Anthropic API status error: %s', exc.status_code)
        return FALLBACK_REPLY, Message.SafetyCategory.NORMAL
    except anthropic.APIConnectionError:
        logger.exception('Anthropic API connection error')
        return FALLBACK_REPLY, Message.SafetyCategory.NORMAL
    except Exception:
        logger.exception('Unexpected error calling Anthropic')
        return FALLBACK_REPLY, Message.SafetyCategory.NORMAL

    reply_text = next(
        (block.text for block in response.content if block.type == 'text'),
        '',
    ).strip()

    if not reply_text:
        logger.warning('Anthropic returned no text content; stop_reason=%s', response.stop_reason)
        return FALLBACK_REPLY, Message.SafetyCategory.NORMAL

    if response.stop_reason == 'refusal':
        return reply_text, Message.SafetyCategory.REFUSED

    safety = _classify_safety(user_message, reply_text)
    return reply_text, safety


def _tidy_title(raw: str) -> str:
    """Clean an AI-generated title: strip quotes/punctuation, cap at 5 words."""
    title = ' '.join(raw.split()).strip().strip('"\'').rstrip('.!?:;,')
    words = title.split()
    if len(words) > 5:
        title = ' '.join(words[:5])
    return title


def generate_title(user_message: str) -> str | None:
    """Ask Claude for a short conversation title. Returns ``None`` on any failure.

    Intentionally cheap: a tiny prompt and a small token budget. The keyword
    classifier in ``title_service`` handles most messages, so this only runs for
    the harder-to-label ones.
    """
    api_key = settings.ANTHROPIC_API_KEY
    if not api_key:
        return None

    max_tokens = getattr(settings, 'CONVERSATION_TITLE_MAX_TOKENS', 20)
    try:
        client = anthropic.Anthropic(api_key=api_key)
        response = client.messages.create(
            model=settings.ANTHROPIC_MODEL,
            max_tokens=max_tokens,
            system=TITLE_SYSTEM_PROMPT,
            messages=[{'role': 'user', 'content': user_message[:500]}],
        )
    except Exception:
        logger.exception('Anthropic title generation failed')
        return None

    raw = next(
        (block.text for block in response.content if block.type == 'text'),
        '',
    ).strip()
    if not raw:
        return None
    return _tidy_title(raw) or None
