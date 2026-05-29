from unittest import mock

from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APITestCase

from .models import Conversation, Message

User = get_user_model()


class ChatAPITest(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='patient', password='pw-12345!')

    def test_chat_requires_authentication(self):
        response = self.client.post('/api/chat/', {'message': 'Hello'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    @mock.patch('apps.chatbot.views.ai_service.generate_reply')
    def test_chat_creates_conversation_and_persists(self, mock_reply):
        mock_reply.return_value = ('Hi there!', Message.SafetyCategory.NORMAL)
        self.client.force_authenticate(self.user)

        response = self.client.post('/api/chat/', {'message': 'Hello'}, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('conversation_id', response.data)
        self.assertEqual(response.data['reply'], 'Hi there!')

        conversation = Conversation.objects.get(user=self.user)
        self.assertEqual(conversation.messages.count(), 2)
        self.assertEqual(conversation.title, 'Hello')

    def test_user_cannot_read_another_users_conversation(self):
        other = User.objects.create_user(username='intruder', password='pw-12345!')
        conversation = Conversation.objects.create(user=other)
        self.client.force_authenticate(self.user)

        response = self.client.get(f'/api/chat/conversations/{conversation.id}/')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
