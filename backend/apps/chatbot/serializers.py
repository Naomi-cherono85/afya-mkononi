from rest_framework import serializers

from .models import ChatMessage, ChatSession


class ChatMessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChatMessage
        fields = [
            'id',
            'session',
            'sender_type',
            'message_content',
            'safety_category',
            'created_at',
        ]
        read_only_fields = ['id', 'session', 'created_at']


class ChatSessionSerializer(serializers.ModelSerializer):
    messages = ChatMessageSerializer(many=True, read_only=True)

    class Meta:
        model = ChatSession
        fields = [
            'session_id',
            'user',
            'started_at',
            'last_active_at',
            'messages',
        ]
        read_only_fields = ['session_id', 'started_at', 'last_active_at']


class ChatRequestSerializer(serializers.Serializer):
    session_id = serializers.UUIDField(required=False, allow_null=True)
    message = serializers.CharField(allow_blank=False, trim_whitespace=True)
