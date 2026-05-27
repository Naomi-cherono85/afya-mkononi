from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from .models import ChatMessage, ChatSession
from .serializers import ChatRequestSerializer, ChatSessionSerializer
from .services import ai_service


@api_view(['POST'])
def chat(request):
    payload = ChatRequestSerializer(data=request.data)
    payload.is_valid(raise_exception=True)

    user_message = payload.validated_data['message']
    session_id = payload.validated_data.get('session_id')
    if session_id:
        session = get_object_or_404(ChatSession, session_id=session_id)
    else:
        session = ChatSession.objects.create()

    ChatMessage.objects.create(
        session=session,
        sender_type=ChatMessage.SenderType.USER,
        message_content=user_message,
        safety_category=ChatMessage.SafetyCategory.NORMAL,
    )

    reply_text, safety_category = ai_service.generate_reply(session, user_message)

    ChatMessage.objects.create(
        session=session,
        sender_type=ChatMessage.SenderType.AI,
        message_content=reply_text,
        safety_category=safety_category,
    )

    session.save(update_fields=['last_active_at'])

    return Response(
        {'session_id': str(session.session_id), 'reply': reply_text},
        status=status.HTTP_200_OK,
    )


@api_view(['GET'])
def session_detail(request, session_id):
    session = get_object_or_404(
        ChatSession.objects.prefetch_related('messages'),
        session_id=session_id,
    )
    return Response(ChatSessionSerializer(session).data)
