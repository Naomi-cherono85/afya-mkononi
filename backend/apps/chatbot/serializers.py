from rest_framework import serializers

from django.core.validators import FileExtensionValidator

from .models import (
    ALLOWED_ATTACHMENT_EXTENSIONS,
    ChatAttachment,
    Conversation,
    Message,
    validate_attachment_size,
)


class ChatAttachmentSerializer(serializers.ModelSerializer):
    url = serializers.SerializerMethodField()
    name = serializers.CharField(read_only=True)
    is_image = serializers.BooleanField(read_only=True)

    class Meta:
        model = ChatAttachment
        fields = ['id', 'url', 'name', 'kind', 'is_image', 'content_type', 'created_at']
        read_only_fields = fields

    def get_url(self, obj):
        if not obj.file:
            return None
        url = obj.file.url
        request = self.context.get('request')
        return request.build_absolute_uri(url) if request else url


class MessageSerializer(serializers.ModelSerializer):
    attachments = ChatAttachmentSerializer(many=True, read_only=True)

    class Meta:
        model = Message
        fields = [
            'id',
            'conversation',
            'sender_type',
            'message_content',
            'safety_category',
            'attachments',
            'created_at',
        ]
        read_only_fields = ['id', 'conversation', 'created_at']


class ConversationSerializer(serializers.ModelSerializer):
    """Full conversation including its messages (used when reopening a chat)."""

    messages = MessageSerializer(many=True, read_only=True)
    display_title = serializers.CharField(read_only=True)

    class Meta:
        model = Conversation
        fields = [
            'id',
            'title',
            'display_title',
            'created_at',
            'updated_at',
            'messages',
        ]
        read_only_fields = fields


class ConversationListSerializer(serializers.ModelSerializer):
    """Lightweight conversation summary for the history sidebar."""

    display_title = serializers.CharField(read_only=True)

    class Meta:
        model = Conversation
        fields = ['id', 'title', 'display_title', 'updated_at']
        read_only_fields = fields


class ConversationRenameSerializer(serializers.ModelSerializer):
    """Validates a user-supplied conversation title for the rename feature."""

    class Meta:
        model = Conversation
        fields = ['title']

    def validate_title(self, value):
        cleaned = ' '.join(value.split())
        if not cleaned:
            raise serializers.ValidationError('Title cannot be empty.')
        return cleaned[:120]


class ChatRequestSerializer(serializers.Serializer):
    conversation_id = serializers.UUIDField(required=False, allow_null=True)
    # Message is now optional: a user may send a file with no accompanying text.
    message = serializers.CharField(
        required=False, allow_blank=True, trim_whitespace=True, default='',
    )
    attachment = serializers.FileField(
        required=False,
        allow_null=True,
        validators=[
            FileExtensionValidator(ALLOWED_ATTACHMENT_EXTENSIONS),
            validate_attachment_size,
        ],
    )

    def validate(self, attrs):
        # Require at least one of text or file so empty submissions are rejected.
        if not (attrs.get('message') or '').strip() and not attrs.get('attachment'):
            raise serializers.ValidationError(
                {'message': 'Enter a message or attach a file.'}
            )
        return attrs
