import base64
import shutil
import tempfile
from unittest import mock

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import SimpleTestCase, override_settings
from rest_framework import status
from rest_framework.test import APITestCase

from .models import ChatAttachment, Conversation, Message
from .services import ai_service
from .services.attachments import extract_document_text
from .services.title_service import generate_conversation_title

User = get_user_model()

# A 1x1 transparent PNG, used to exercise the image (vision) path.
_PNG_1PX = base64.b64decode(
    'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk'
    '+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=='
)


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

    @mock.patch('apps.chatbot.services.ai_service.generate_title', return_value=None)
    @mock.patch('apps.chatbot.views.ai_service.generate_reply')
    def test_chat_response_includes_safety_category(self, mock_reply, _mock_title):
        mock_reply.return_value = ('Please call 999.', Message.SafetyCategory.EMERGENCY)
        self.client.force_authenticate(self.user)
        response = self.client.post('/api/chat/', {'message': 'chest pain'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Exposed so the client can suppress follow-up chips on emergencies.
        self.assertEqual(response.data['safety_category'], Message.SafetyCategory.EMERGENCY)
        self.assertIsNone(response.data['attachment'])

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


_TMP_MEDIA = tempfile.mkdtemp(prefix='afya-test-media-')


@override_settings(MEDIA_ROOT=_TMP_MEDIA)
class MultimodalChatTest(APITestCase):
    """Image + document upload handling (file storage stays in a temp dir)."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.addClassCleanup(shutil.rmtree, _TMP_MEDIA, ignore_errors=True)

    def setUp(self):
        self.user = User.objects.create_user(username='patient', password='pw-12345!')
        self.client.force_authenticate(self.user)

    @mock.patch('apps.chatbot.services.ai_service.generate_title', return_value=None)
    @mock.patch('apps.chatbot.views.ai_service.generate_reply')
    def test_document_upload_extracts_text_and_persists_attachment(self, mock_reply, _t):
        mock_reply.return_value = ('Here is a summary.', Message.SafetyCategory.NORMAL)
        doc = SimpleUploadedFile(
            'report.txt', b'Patient haemoglobin level is normal.', content_type='text/plain',
        )

        response = self.client.post(
            '/api/chat/',
            {'message': 'Please explain this report', 'attachment': doc},
            format='multipart',
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        attachment = ChatAttachment.objects.get()
        self.assertEqual(attachment.kind, ChatAttachment.Kind.DOCUMENT)
        self.assertIn('haemoglobin', attachment.extracted_text)
        # The attachment object is handed to the AI service.
        self.assertEqual(mock_reply.call_args.kwargs['attachment'], attachment)

    @mock.patch('apps.chatbot.services.ai_service.generate_title', return_value=None)
    @mock.patch('apps.chatbot.views.ai_service.generate_reply')
    def test_image_upload_creates_image_attachment(self, mock_reply, _t):
        mock_reply.return_value = ('General guidance only.', Message.SafetyCategory.NORMAL)
        img = SimpleUploadedFile('rash.png', _PNG_1PX, content_type='image/png')

        response = self.client.post(
            '/api/chat/',
            {'message': 'What might this be?', 'attachment': img},
            format='multipart',
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        attachment = ChatAttachment.objects.get()
        self.assertEqual(attachment.kind, ChatAttachment.Kind.IMAGE)
        self.assertTrue(attachment.is_image)
        self.assertEqual(attachment.media_type, 'image/png')

    @mock.patch('apps.chatbot.views.ai_service.generate_reply')
    def test_disallowed_file_type_is_rejected(self, mock_reply):
        bad = SimpleUploadedFile('malware.exe', b'MZ...', content_type='application/octet-stream')
        response = self.client.post('/api/chat/', {'attachment': bad}, format='multipart')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        mock_reply.assert_not_called()

    @mock.patch('apps.chatbot.views.ai_service.generate_reply')
    def test_oversized_file_is_rejected(self, mock_reply):
        big = SimpleUploadedFile('huge.txt', b'x' * (10 * 1024 * 1024 + 1), content_type='text/plain')
        response = self.client.post('/api/chat/', {'attachment': big}, format='multipart')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        mock_reply.assert_not_called()

    def test_attachment_returned_in_conversation_detail(self):
        conversation = Conversation.objects.create(user=self.user)
        message = Message.objects.create(
            conversation=conversation,
            sender_type=Message.SenderType.USER,
            message_content='see attached',
        )
        ChatAttachment.objects.create(
            message=message,
            file=SimpleUploadedFile('note.txt', b'hello', content_type='text/plain'),
            original_name='note.txt',
            kind=ChatAttachment.Kind.DOCUMENT,
        )

        response = self.client.get(f'/api/chat/conversations/{conversation.id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        attachments = response.data['messages'][0]['attachments']
        self.assertEqual(len(attachments), 1)
        self.assertEqual(attachments[0]['name'], 'note.txt')
        self.assertFalse(attachments[0]['is_image'])

    def test_build_user_content_image_returns_vision_block(self):
        message = Message.objects.create(
            conversation=Conversation.objects.create(user=self.user),
            sender_type=Message.SenderType.USER,
        )
        attachment = ChatAttachment.objects.create(
            message=message,
            file=SimpleUploadedFile('x.png', _PNG_1PX, content_type='image/png'),
            original_name='x.png',
            kind=ChatAttachment.Kind.IMAGE,
        )

        content = ai_service._build_user_content('What is this?', attachment)
        self.assertIsInstance(content, list)
        self.assertEqual(content[0]['type'], 'image')
        self.assertEqual(content[0]['source']['media_type'], 'image/png')
        self.assertEqual(content[1]['text'], 'What is this?')

    def test_build_user_content_document_folds_in_text(self):
        message = Message.objects.create(
            conversation=Conversation.objects.create(user=self.user),
            sender_type=Message.SenderType.USER,
        )
        attachment = ChatAttachment.objects.create(
            message=message,
            file=SimpleUploadedFile('r.txt', b'glucose 5.4', content_type='text/plain'),
            original_name='r.txt',
            kind=ChatAttachment.Kind.DOCUMENT,
            extracted_text='glucose 5.4',
        )

        content = ai_service._build_user_content('Summarise', attachment)
        self.assertIsInstance(content, str)
        self.assertIn('glucose 5.4', content)
        self.assertIn('Summarise', content)


@override_settings(MEDIA_ROOT=_TMP_MEDIA)
class DocumentExtractionTest(APITestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.addClassCleanup(shutil.rmtree, _TMP_MEDIA, ignore_errors=True)

    def setUp(self):
        self.user = User.objects.create_user(username='reader', password='pw-12345!')

    def _attachment(self, name, data):
        message = Message.objects.create(
            conversation=Conversation.objects.create(user=self.user),
            sender_type=Message.SenderType.USER,
        )
        ext = name.rsplit('.', 1)[-1].lower()
        return ChatAttachment.objects.create(
            message=message,
            file=SimpleUploadedFile(name, data, content_type='application/octet-stream'),
            original_name=name,
            kind=ChatAttachment.kind_for_extension(ext),
        )

    def test_txt_extraction(self):
        att = self._attachment('a.txt', b'Take with food. Avoid alcohol.')
        self.assertEqual(extract_document_text(att), 'Take with food. Avoid alcohol.')

    def test_docx_extraction(self):
        import docx
        import io

        buf = io.BytesIO()
        document = docx.Document()
        document.add_paragraph('Diagnosis pending. Follow up in two weeks.')
        document.save(buf)
        att = self._attachment('a.docx', buf.getvalue())
        self.assertIn('Follow up in two weeks', extract_document_text(att))


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
