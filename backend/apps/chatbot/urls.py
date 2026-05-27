from django.urls import path

from .views import chat, session_detail

urlpatterns = [
    path('chat/', chat, name='chat'),
    path('chat/sessions/<uuid:session_id>/', session_detail, name='chat-session-detail'),
]
