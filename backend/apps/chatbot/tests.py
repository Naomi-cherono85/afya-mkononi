from unittest import mock

from django.contrib.auth import get_user_model
from django.test import SimpleTestCase
from rest_framework import status
from rest_framework.test import APITestCase

from .models import Conversation, Message
from .services.title_service import generate_conversation_title

User = get_user_model()


class ChatAPITest(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='patient', password='pw-12345!')

    def test_chat_requires_authentication(self):
        response = self.client.post('/api/chat/', {'message': 'Hello'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    @mock.patch('apps.chatbot.services.ai_service.generate_title', return_value=None)
    @mock.patch('apps.chatbot.views.ai_service.generate_reply')
    def test_chat_creates_conversation_and_persists(self, mock_reply, _mock_title):
        mock_reply.return_value = ('Hi there!', Message.SafetyCategory.NORMAL)
        self.client.force_authenticate(self.user)

        response = self.client.post('/api/chat/', {'message': 'Hello'}, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('conversation_id', response.data)
        self.assertEqual(response.data['reply'], 'Hi there!')

        conversation = Conversation.objects.get(user=self.user)
        self.assertEqual(conversation.messages.count(), 2)
        # 'Hello' matches no keyword and the AI step is stubbed off, so the
        # cleaned-message fallback is used.
        self.assertEqual(conversation.title, 'Hello')

    @mock.patch('apps.chatbot.services.ai_service.generate_title', return_value=None)
    @mock.patch('apps.chatbot.views.ai_service.generate_reply')
    def test_chat_titles_conversation_by_topic(self, mock_reply, _mock_title):
        mock_reply.return_value = ('Sure.', Message.SafetyCategory.NORMAL)
        self.client.force_authenticate(self.user)

        self.client.post(
            '/api/chat/',
            {'message': 'I have a headache. What could be the cause?'},
            format='json',
        )

        conversation = Conversation.objects.get(user=self.user)
        self.assertEqual(conversation.title, 'Headache Assessment')

    def test_rename_conversation(self):
        self.client.force_authenticate(self.user)
        conversation = Conversation.objects.create(user=self.user, title='Old title')

        response = self.client.patch(
            f'/api/chat/conversations/{conversation.id}/',
            {'title': '  Migraine follow-up  '},
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['title'], 'Migraine follow-up')
        conversation.refresh_from_db()
        self.assertEqual(conversation.title, 'Migraine follow-up')

    def test_rename_rejects_blank_title(self):
        self.client.force_authenticate(self.user)
        conversation = Conversation.objects.create(user=self.user, title='Keep me')

        response = self.client.patch(
            f'/api/chat/conversations/{conversation.id}/',
            {'title': '   '},
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        conversation.refresh_from_db()
        self.assertEqual(conversation.title, 'Keep me')

    def test_cannot_rename_another_users_conversation(self):
        other = User.objects.create_user(username='snoop', password='pw-12345!')
        conversation = Conversation.objects.create(user=other, title='Theirs')
        self.client.force_authenticate(self.user)

        response = self.client.patch(
            f'/api/chat/conversations/{conversation.id}/',
            {'title': 'Mine now'},
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_user_cannot_read_another_users_conversation(self):
        other = User.objects.create_user(username='intruder', password='pw-12345!')
        conversation = Conversation.objects.create(user=other)
        self.client.force_authenticate(self.user)

        response = self.client.get(f'/api/chat/conversations/{conversation.id}/')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class TitleGenerationTest(SimpleTestCase):
    """Keyword-based title classification (no DB, no network)."""

    CASES = {
        'I have a headache and body pain': 'Headache Assessment',
        'What causes chest pain?': 'Chest Pain Guidance',
        'Can I take paracetamol while pregnant?': 'Medication Safety',
        'How do I book an appointment?': 'Appointment Booking',
        'What are the symptoms of malaria?': 'Malaria Information',
        'Remind me to take my medication': 'Medication Reminder',
        "I've been coughing for a week": 'Persistent Cough',
        'How can I lower my blood pressure?': 'Blood Pressure Guidance',
        'I have a headache. What could be the cause?': 'Headache Assessment',
        'Remind me to take my medication every day': 'Medication Reminder',
        "I've had a fever for 3 days": 'Fever Consultation',
    }

    def test_keyword_classification(self):
        for message, expected in self.CASES.items():
            with self.subTest(message=message):
                self.assertEqual(
                    generate_conversation_title(message, use_ai=False),
                    expected,
                )

    def test_blank_message_returns_empty(self):
        self.assertEqual(generate_conversation_title('   ', use_ai=False), '')

    def test_unknown_message_falls_back_to_cleaned_text(self):
        # No keyword match and AI disabled -> cleaned, shortened first message.
        title = generate_conversation_title(
            'Hello there, I just wanted to say a quick friendly hi to everyone',
            use_ai=False,
        )
        self.assertTrue(title.startswith('Hello there'))
        self.assertLessEqual(len(title), 50)
