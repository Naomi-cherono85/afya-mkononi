from django.urls import path

from .views import chat, conversation_detail, conversation_list

urlpatterns = [
    path('chat/', chat, name='chat'),
    path('chat/conversations/', conversation_list, name='conversation-list'),
    path('chat/conversations/<uuid:conversation_id>/', conversation_detail, name='conversation-detail'),
]
