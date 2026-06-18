import os
import uuid

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import FileExtensionValidator
from django.db import models

# Attachment policy, shared by the model field and the chat serializer so the
# rules live in exactly one place.
ALLOWED_ATTACHMENT_EXTENSIONS = ['jpg', 'jpeg', 'png', 'webp', 'pdf', 'docx', 'txt']
IMAGE_ATTACHMENT_EXTENSIONS = {'jpg', 'jpeg', 'png', 'webp'}
DOCUMENT_ATTACHMENT_EXTENSIONS = {'pdf', 'docx', 'txt'}
MAX_ATTACHMENT_SIZE = 10 * 1024 * 1024  # 10 MB

# Anthropic media types keyed by file extension (vision-capable image formats).
IMAGE_MEDIA_TYPES = {
    'jpg': 'image/jpeg',
    'jpeg': 'image/jpeg',
    'png': 'image/png',
    'webp': 'image/webp',
}


def validate_attachment_size(value):
    """Reject oversized uploads (DRF runs field validators before saving)."""
    if value.size > MAX_ATTACHMENT_SIZE:
        raise ValidationError('Attachment is too large (maximum 10 MB).')


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
        """Generate a short, professional title from the first user message.

        Only runs when the conversation has no title yet, so existing
        conversations and manual renames are never overwritten. Title
        generation lives in ``services.title_service`` (keyword classification
        with an optional AI step and a graceful fallback).
        """
        if self.title:
            return
        # Lazy import: services import models, so importing at module load
        # would create a circular import.
        from apps.chatbot.services.title_service import generate_conversation_title
        title = generate_conversation_title(text)
        if not title:
            return
        self.title = title[:120]
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
    message_content = models.TextField(blank=True)
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
        preview = self.message_content[:40] or '(empty)'
        return f"[{self.sender_type}/{self.safety_category}] {preview} ({self.created_at:%Y-%m-%d %H:%M})"

    @property
    def has_attachments(self):
        return self.attachments.exists()


class ChatAttachment(models.Model):
    """A file uploaded with a chat message (image or text document).

    Files are stored under ``MEDIA_ROOT/chat_attachments/YYYY/MM/``. Images are
    sent to the AI as vision input; documents (PDF/DOCX/TXT) have their text
    extracted into ``extracted_text`` and that text is fed into the prompt.
    """

    class Kind(models.TextChoices):
        IMAGE = 'IMAGE', 'Image'
        DOCUMENT = 'DOCUMENT', 'Document'

    message = models.ForeignKey(
        Message,
        on_delete=models.CASCADE,
        related_name='attachments',
    )
    file = models.FileField(
        upload_to='chat_attachments/%Y/%m/',
        validators=[
            FileExtensionValidator(ALLOWED_ATTACHMENT_EXTENSIONS),
            validate_attachment_size,
        ],
    )
    original_name = models.CharField(max_length=255, blank=True)
    content_type = models.CharField(max_length=100, blank=True)
    kind = models.CharField(
        max_length=10,
        choices=Kind.choices,
        default=Kind.DOCUMENT,
    )
    # Populated for documents (PDF/DOCX/TXT) so we don't re-parse on every turn.
    extracted_text = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f"{self.get_kind_display()}: {self.name}"

    @property
    def name(self):
        """Best display name: the original upload name, else the stored name."""
        return self.original_name or os.path.basename(self.file.name)

    @property
    def extension(self):
        return self.file.name.rsplit('.', 1)[-1].lower() if self.file else ''

    @property
    def is_image(self):
        return self.extension in IMAGE_ATTACHMENT_EXTENSIONS

    @property
    def is_document(self):
        return self.extension in DOCUMENT_ATTACHMENT_EXTENSIONS

    @property
    def media_type(self):
        """Anthropic media type for images (e.g. 'image/jpeg'); '' otherwise."""
        return IMAGE_MEDIA_TYPES.get(self.extension, '')

    @property
    def url(self):
        return self.file.url if self.file else ''

    @classmethod
    def kind_for_extension(cls, ext):
        return cls.Kind.IMAGE if ext.lower() in IMAGE_ATTACHMENT_EXTENSIONS else cls.Kind.DOCUMENT
