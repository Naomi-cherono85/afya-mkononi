from django.conf import settings
from django.db import models


class Profile(models.Model):
    """Extra patient information attached one-to-one to the auth User.

    A profile is auto-created for every user via a post_save signal
    (see ``apps.accounts.signals``), so ``user.profile`` is always available.
    """

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='profile',
    )
    avatar = models.ImageField(
        upload_to='avatars/',
        blank=True,
        help_text='Optional profile photo. Initials are shown when empty.',
    )
    phone_number = models.CharField(max_length=20, blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'Profile for {self.user.get_username()}'

    @property
    def display_name(self):
        """Full name when available, otherwise the username."""
        full = self.user.get_full_name().strip()
        return full or self.user.get_username()

    @property
    def initials(self):
        """Up to two initials for the fallback avatar circle."""
        full = self.user.get_full_name().strip()
        if full:
            parts = full.split()
            letters = parts[0][:1] + (parts[-1][:1] if len(parts) > 1 else '')
        else:
            letters = self.user.get_username()[:2]
        return letters.upper()
