import io
import shutil
import tempfile

from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.urls import reverse

from apps.accounts.models import Profile

User = get_user_model()

MEDIA = tempfile.mkdtemp()


def _png_bytes():
    """Return the bytes of a tiny valid PNG (needs Pillow, already a dependency)."""
    from PIL import Image
    buf = io.BytesIO()
    Image.new('RGB', (2, 2), '#10b981').save(buf, format='PNG')
    buf.seek(0)
    return buf.read()


@override_settings(MEDIA_ROOT=MEDIA)
class ProfileTests(TestCase):
    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(MEDIA, ignore_errors=True)
        super().tearDownClass()

    def setUp(self):
        self.user = User.objects.create_user('naomi', password='pass12345')
        self.client.force_login(self.user)
        self.url = reverse('accounts:profile')

    def test_profile_auto_created(self):
        self.assertTrue(Profile.objects.filter(user=self.user).exists())

    def test_edit_details(self):
        resp = self.client.post(self.url, {
            'action': 'save_details',
            'first_name': 'Naomi', 'last_name': 'C', 'email': 'n@example.com',
            'phone_number': '+254700000000', 'gender': 'FEMALE', 'date_of_birth': '',
        })
        self.assertRedirects(resp, self.url)
        self.user.refresh_from_db()
        self.assertEqual(self.user.first_name, 'Naomi')
        self.assertEqual(self.user.profile.gender, 'FEMALE')
        self.assertEqual(self.user.profile.phone_number, '+254700000000')

    def test_choose_builtin_avatar(self):
        resp = self.client.post(self.url, {'action': 'choose_avatar', 'avatar_choice': 'avatar-blue'})
        self.assertRedirects(resp, self.url)
        self.user.profile.refresh_from_db()
        self.assertEqual(self.user.profile.avatar_choice, 'avatar-blue')
        self.assertIn('avatar-blue.svg', self.user.profile.avatar_display_url)

    def test_invalid_builtin_avatar_ignored(self):
        self.client.post(self.url, {'action': 'choose_avatar', 'avatar_choice': 'not-real'})
        self.user.profile.refresh_from_db()
        self.assertEqual(self.user.profile.avatar_choice, '')

    def test_upload_avatar_supersedes_builtin(self):
        from django.core.files.uploadedfile import SimpleUploadedFile
        # start with a built-in selected
        self.user.profile.avatar_choice = 'avatar-blue'
        self.user.profile.save()
        img = SimpleUploadedFile('me.png', _png_bytes(), content_type='image/png')
        resp = self.client.post(self.url, {'action': 'upload_avatar', 'avatar': img})
        self.assertRedirects(resp, self.url)
        self.user.profile.refresh_from_db()
        self.assertTrue(self.user.profile.avatar)
        self.assertEqual(self.user.profile.avatar_choice, '')  # cleared by upload
        self.assertIn(self.user.profile.avatar.url, self.user.profile.avatar_display_url)

    def test_delete_avatar_falls_back_to_initials(self):
        self.user.profile.avatar_choice = 'avatar-green'
        self.user.profile.save()
        resp = self.client.post(self.url, {'action': 'delete_avatar'})
        self.assertRedirects(resp, self.url)
        self.user.profile.refresh_from_db()
        self.assertEqual(self.user.profile.avatar_choice, '')
        self.assertFalse(self.user.profile.avatar)
        self.assertEqual(self.user.profile.avatar_display_url, '')  # → initials in template

    def test_initials(self):
        self.user.first_name = 'Naomi'
        self.user.last_name = 'Cherono'
        self.user.save()
        self.assertEqual(self.user.profile.initials, 'NC')
