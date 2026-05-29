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

STYLE
- 2-4 short paragraphs is usually enough.
- If a question is outside healthcare, briefly redirect to health-related help.
- End informational answers with a gentle nudge to consult a healthcare professional when relevant.
"""

FALLBACK_REPLY = (
    "I'm having trouble reaching my assistant right now. Please try again in a moment. "
    "If this is a medical emergency, call 999 or 112, or go to the nearest hospital immediately."
)

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
        messages.append({
            'role': role_map[msg.sender_type],
            'content': msg.message_content,
        })
    return messages


def generate_reply(conversation: Conversation, user_message: str) -> Tuple[str, str]:
    """Generate a Claude reply for the given conversation and new user message.

    Returns (reply_text, safety_category). On any API failure returns a safe
    fallback so the chat flow never breaks.

    The caller persists both the user message (before this call) and the
    returned AI message — ai_service.py does not touch the database.
    """
    api_key = settings.ANTHROPIC_API_KEY
    if not api_key:
        logger.error('ANTHROPIC_API_KEY is empty; falling back.')
        return FALLBACK_REPLY, Message.SafetyCategory.NORMAL

    history = _build_history(conversation, settings.ANTHROPIC_HISTORY_TURNS)
    history.append({'role': 'user', 'content': user_message})

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
