from rest_framework import serializers

from .models import Conversation, Message


class MessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Message
        fields = [
            'id',
            'conversation',
            'sender_type',
            'message_content',
            'safety_category',
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
    message = serializers.CharField(allow_blank=False, trim_whitespace=True)
