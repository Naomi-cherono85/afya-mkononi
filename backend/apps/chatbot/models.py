import uuid

from django.conf import settings
from django.db import models


class ChatSession(models.Model):
    session_id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='chat_sessions',
    )
    started_at = models.DateTimeField(auto_now_add=True)
    last_active_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-last_active_at']
        indexes = [
            models.Index(fields=['last_active_at']),
        ]

    def __str__(self):
        return f"Session {self.session_id} (last active {self.last_active_at:%Y-%m-%d %H:%M})"


class ChatMessage(models.Model):
    class SenderType(models.TextChoices):
        USER = 'USER', 'User'
        AI = 'AI', 'AI'
        SYSTEM = 'SYSTEM', 'System'

    class SafetyCategory(models.TextChoices):
        NORMAL = 'NORMAL', 'Normal'
        EMERGENCY = 'EMERGENCY', 'Emergency'
        REFUSED = 'REFUSED', 'Refused'
        ESCALATED = 'ESCALATED', 'Escalated'

    session = models.ForeignKey(
        ChatSession,
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
            models.Index(fields=['session', 'created_at']),
            models.Index(fields=['safety_category']),
        ]

    def __str__(self):
        preview = self.message_content[:40]
        return f"[{self.sender_type}/{self.safety_category}] {preview} ({self.created_at:%Y-%m-%d %H:%M})"
