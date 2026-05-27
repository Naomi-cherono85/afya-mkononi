from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from .models import ChatMessage, ChatSession
from .serializers import ChatRequestSerializer, ChatSessionSerializer

PLACEHOLDER_AI_REPLY = "AI integration coming in Week 3"


@api_view(['POST'])
def chat(request):
    payload = ChatRequestSerializer(data=request.data)
    payload.is_valid(raise_exception=True)

    session_id = payload.validated_data.get('session_id')
    if session_id:
        session = get_object_or_404(ChatSession, session_id=session_id)
    else:
        session = ChatSession.objects.create()

    ChatMessage.objects.create(
        session=session,
        sender_type=ChatMessage.SenderType.USER,
        message_content=payload.validated_data['message'],
        safety_category=ChatMessage.SafetyCategory.NORMAL,
    )

    ChatMessage.objects.create(
        session=session,
        sender_type=ChatMessage.SenderType.AI,
        message_content=PLACEHOLDER_AI_REPLY,
        safety_category=ChatMessage.SafetyCategory.NORMAL,
    )

    session.save(update_fields=['last_active_at'])

    return Response(
        {'session_id': str(session.session_id), 'reply': PLACEHOLDER_AI_REPLY},
        status=status.HTTP_200_OK,
    )


@api_view(['GET'])
def session_detail(request, session_id):
    session = get_object_or_404(
        ChatSession.objects.prefetch_related('messages'),
        session_id=session_id,
    )
    return Response(ChatSessionSerializer(session).data)
