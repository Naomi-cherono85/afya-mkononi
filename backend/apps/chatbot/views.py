from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import ChatAttachment, Conversation, Message
from .serializers import (
    ChatAttachmentSerializer,
    ChatRequestSerializer,
    ConversationListSerializer,
    ConversationRenameSerializer,
    ConversationSerializer,
)
from .services import ai_service
from .services import attachments as attachment_service


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def chat(request):
    """Send a message; create or continue the user's conversation."""
    payload = ChatRequestSerializer(data=request.data)
    payload.is_valid(raise_exception=True)

    user_message = payload.validated_data.get('message', '').strip()
    attachment = payload.validated_data.get('attachment')
    conversation_id = payload.validated_data.get('conversation_id')

    if conversation_id:
        # Ownership-scoped: a user can only post into their own conversation.
        conversation = get_object_or_404(
            Conversation, id=conversation_id, user=request.user,
        )
    else:
        conversation = Conversation.objects.create(user=request.user)

    user_msg = Message.objects.create(
        conversation=conversation,
        sender_type=Message.SenderType.USER,
        message_content=user_message,
        safety_category=Message.SafetyCategory.NORMAL,
    )

    # Persist the upload as a ChatAttachment and, for documents, extract text now
    # so the AI service receives ready-to-use content.
    chat_attachment = None
    if attachment:
        ext = attachment.name.rsplit('.', 1)[-1].lower()
        chat_attachment = ChatAttachment(
            message=user_msg,
            file=attachment,
            original_name=attachment.name,
            content_type=getattr(attachment, 'content_type', '') or '',
            kind=ChatAttachment.kind_for_extension(ext),
        )
        chat_attachment.save()
        if chat_attachment.is_document:
            chat_attachment.extracted_text = attachment_service.extract_document_text(
                chat_attachment
            )
            chat_attachment.save(update_fields=['extracted_text'])

    # Title the thread from its first user message (ChatGPT-style). Fall back to
    # the filename when the message is attachment-only.
    title_seed = user_message or (
        f"Shared {chat_attachment.name}" if chat_attachment else ''
    )
    conversation.set_title_from(title_seed)

    reply_text, safety_category = ai_service.generate_reply(
        conversation, user_message, attachment=chat_attachment,
    )

    Message.objects.create(
        conversation=conversation,
        sender_type=Message.SenderType.AI,
        message_content=reply_text,
        safety_category=safety_category,
    )

    # Bump updated_at so the conversation rises to the top of the history list.
    conversation.save(update_fields=['updated_at'])

    attachment_data = (
        ChatAttachmentSerializer(chat_attachment, context={'request': request}).data
        if chat_attachment else None
    )

    return Response(
        {
            'conversation_id': str(conversation.id),
            'title': conversation.display_title,
            'reply': reply_text,
            # Lets the client suppress follow-up chips on emergency/refused replies.
            'safety_category': safety_category,
            # Echoes the just-uploaded file so the sent message can preview it inline.
            'attachment': attachment_data,
        },
        status=status.HTTP_200_OK,
    )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def conversation_list(request):
    """List the signed-in user's conversations for the history sidebar."""
    conversations = request.user.conversations.all()
    return Response(ConversationListSerializer(conversations, many=True).data)


@api_view(['GET', 'PATCH'])
@permission_classes([IsAuthenticated])
def conversation_detail(request, conversation_id):
    """Return one conversation (GET) or rename it (PATCH), scoped to the owner."""
    conversation = get_object_or_404(
        Conversation.objects.prefetch_related('messages__attachments'),
        id=conversation_id,
        user=request.user,
    )

    if request.method == 'PATCH':
        serializer = ConversationRenameSerializer(
            conversation, data=request.data, partial=True,
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(ConversationListSerializer(conversation).data)

    return Response(ConversationSerializer(conversation).data)
