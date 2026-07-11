from django.conf import settings
from django.db import models
from django.templatetags.static import static


# Built-in, healthcare-themed avatars a user can pick instead of uploading a
# photo. Keys map to SVG files under ``theme/static/images/avatars/<key>.svg``.
BUILTIN_AVATARS = [
    ('avatar-teal', 'Teal'),
    ('avatar-blue', 'Blue'),
    ('avatar-green', 'Green'),
    ('avatar-amber', 'Amber'),
    ('avatar-rose', 'Rose'),
    ('avatar-violet', 'Violet'),
]
BUILTIN_AVATAR_KEYS = {key for key, _ in BUILTIN_AVATARS}


class Profile(models.Model):
    """Extra patient information attached one-to-one to the auth User.

    A profile is auto-created for every user via a post_save signal
    (see ``apps.accounts.signals``), so ``user.profile`` is always available.
    """

    class Gender(models.TextChoices):
        MALE = 'MALE', 'Male'
        FEMALE = 'FEMALE', 'Female'
        OTHER = 'OTHER', 'Other'
        PREFER_NOT = 'PREFER_NOT', 'Prefer not to say'

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
    avatar_choice = models.CharField(
        max_length=32,
        blank=True,
        help_text='Key of a chosen built-in avatar. Ignored when a photo is uploaded.',
    )
    phone_number = models.CharField(max_length=20, blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    gender = models.CharField(
        max_length=12,
        choices=Gender.choices,
        blank=True,
    )
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

    @property
    def avatar_display_url(self):
        """URL to show for this profile, or '' to fall back to initials.

        Precedence: an uploaded photo wins, then a chosen built-in avatar,
        then nothing (templates render the initials circle instead).
        """
        if self.avatar:
            return self.avatar.url
        if self.avatar_choice in BUILTIN_AVATAR_KEYS:
            return static(f'images/avatars/{self.avatar_choice}.svg')
        return ''
