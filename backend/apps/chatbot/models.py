import uuid

from django.conf import settings
from django.db import models


class Conversation(models.Model):
    """A single chat thread between a user and the assistant.

    Replaces the older anonymous ``ChatSession``: conversations are now owned by
    a user, carry a human-readable ``title``, and power the ChatGPT-style history
    sidebar. ``needs_human`` is reserved scaffolding for the future care-team
    escalation flow (see ``apps.chatbot.services.escalation``) and is not yet
    driven by any logic.
    """

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='conversations',
    )
    title = models.CharField(max_length=120, blank=True)
    needs_human = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-updated_at']
        indexes = [
            models.Index(fields=['user', '-updated_at'], name='conv_user_updated_idx'),
            models.Index(fields=['-updated_at'], name='conv_updated_idx'),
        ]

    def __str__(self):
        return f"{self.display_title} ({self.updated_at:%Y-%m-%d %H:%M})"

    @property
    def display_title(self):
        return self.title or 'New conversation'

    def set_title_from(self, text, *, save=True):
        """Derive a short title from the first user message, if not already set."""
        if self.title:
            return
        cleaned = ' '.join(text.split())
        self.title = (cleaned[:57] + '...') if len(cleaned) > 60 else cleaned
        if save:
            self.save(update_fields=['title'])


class Message(models.Model):
    class SenderType(models.TextChoices):
        USER = 'USER', 'User'
        AI = 'AI', 'AI'
        SYSTEM = 'SYSTEM', 'System'

    class SafetyCategory(models.TextChoices):
        NORMAL = 'NORMAL', 'Normal'
        EMERGENCY = 'EMERGENCY', 'Emergency'
        REFUSED = 'REFUSED', 'Refused'
        ESCALATED = 'ESCALATED', 'Escalated'

    conversation = models.ForeignKey(
        Conversation,
        on_delete=models.CASCADE,
        related_name='messages',
    )
    sender_type = models.CharField(
        max_length=10,
        choices=SenderType.choices,
    )
    message_content = models.TextField()
    safety_category = models.CharField(
        max_length=20,
        choices=SafetyCategory.choices,
        default=SafetyCategory.NORMAL,
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']
        indexes = [
            models.Index(fields=['conversation', 'created_at'], name='msg_conv_created_idx'),
            models.Index(fields=['safety_category'], name='msg_safety_idx'),
        ]

    def __str__(self):
        preview = self.message_content[:40]
        return f"[{self.sender_type}/{self.safety_category}] {preview} ({self.created_at:%Y-%m-%d %H:%M})"
