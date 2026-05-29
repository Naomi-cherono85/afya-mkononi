from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import Conversation, Message
from .serializers import (
    ChatRequestSerializer,
    ConversationListSerializer,
    ConversationSerializer,
)
from .services import ai_service


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def chat(request):
    """Send a message; create or continue the user's conversation."""
    payload = ChatRequestSerializer(data=request.data)
    payload.is_valid(raise_exception=True)

    user_message = payload.validated_data['message']
    conversation_id = payload.validated_data.get('conversation_id')

    if conversation_id:
        # Ownership-scoped: a user can only post into their own conversation.
        conversation = get_object_or_404(
            Conversation, id=conversation_id, user=request.user,
        )
    else:
        conversation = Conversation.objects.create(user=request.user)

    Message.objects.create(
        conversation=conversation,
        sender_type=Message.SenderType.USER,
        message_content=user_message,
        safety_category=Message.SafetyCategory.NORMAL,
    )

    # Title the thread from its first user message (ChatGPT-style).
    conversation.set_title_from(user_message)

    reply_text, safety_category = ai_service.generate_reply(conversation, user_message)

    Message.objects.create(
        conversation=conversation,
        sender_type=Message.SenderType.AI,
        message_content=reply_text,
        safety_category=safety_category,
    )

    # Bump updated_at so the conversation rises to the top of the history list.
    conversation.save(update_fields=['updated_at'])

    return Response(
        {
            'conversation_id': str(conversation.id),
            'title': conversation.display_title,
            'reply': reply_text,
        },
        status=status.HTTP_200_OK,
    )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def conversation_list(request):
    """List the signed-in user's conversations for the history sidebar."""
    conversations = request.user.conversations.all()
    return Response(ConversationListSerializer(conversations, many=True).data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def conversation_detail(request, conversation_id):
    """Return one conversation with its messages, scoped to the owner."""
    conversation = get_object_or_404(
        Conversation.objects.prefetch_related('messages'),
        id=conversation_id,
        user=request.user,
    )
    return Response(ConversationSerializer(conversation).data)
