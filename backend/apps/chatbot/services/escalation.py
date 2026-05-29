"""Care-team escalation scaffolding (NOT YET WIRED).

This module sketches the future "Talk to a Healthcare Professional" flow so the
rest of the codebase can grow toward it without committing to an implementation
now. None of these functions are called from views, signals, or tasks yet — the
chat flow is unaffected.

Intended future flow
---------------------
1. After each AI turn, ``should_escalate(conversation)`` decides whether the
   assistant is out of its depth (repeated REFUSED/ESCALATED safety tags,
   explicit user request for a human, low-confidence answers, etc.).
2. If so, the UI offers the patient a "Talk to a Healthcare Professional"
   action. Accepting flips ``Conversation.needs_human = True``.
3. ``build_conversation_summary(conversation)`` produces a concise, PII-aware
   summary of the thread for a nurse to triage.
4. ``notify_care_team(summary, channel)`` delivers it — to a WhatsApp number
   (reusing ``apps.core.SiteSettings.whatsapp_number``) or a future internal
   nurse dashboard.

Reuses existing schema: ``Conversation.needs_human`` and
``Message.SafetyCategory.ESCALATED`` are already defined for this purpose.
"""

from __future__ import annotations

# Sentinel safety categories that, when seen, would weigh toward escalation.
ESCALATION_SIGNALS = ('REFUSED', 'ESCALATED', 'EMERGENCY')


def should_escalate(conversation) -> bool:
    """Decide whether a conversation should be handed to a human.

    NOT IMPLEMENTED. Placeholder returns False so nothing escalates today.
    Future logic will inspect recent ``Message.safety_category`` values and
    explicit user requests.
    """
    return False


def build_conversation_summary(conversation) -> str:
    """Produce a short, triage-ready summary of the conversation for a nurse.

    NOT IMPLEMENTED. Will likely call the AI service with a summarisation
    prompt over ``conversation.messages``.
    """
    raise NotImplementedError('Conversation summarisation is not implemented yet.')


def notify_care_team(summary: str, channel: str = 'whatsapp') -> None:
    """Deliver a conversation summary to the care team.

    NOT IMPLEMENTED. Target channels are 'whatsapp' (via the number in
    ``apps.core.SiteSettings``) or a future 'dashboard'.
    """
    raise NotImplementedError('Care-team notification is not implemented yet.')
