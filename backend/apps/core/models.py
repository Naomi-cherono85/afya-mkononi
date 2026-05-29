from urllib.parse import quote

from django.core.exceptions import ValidationError
from django.db import models


class SiteSettings(models.Model):
    """Single-row, admin-editable site configuration.

    Holds values that non-technical administrators need to change without a
    redeploy — currently the human-support WhatsApp number and care-team
    presentation. Always access via ``SiteSettings.load()`` so templates and
    services share one consistent instance.
    """

    SINGLETON_PK = 1

    care_team_name = models.CharField(
        max_length=120,
        default='Afya Mkononi Care Team',
        help_text='Display name for the human support team.',
    )
    whatsapp_number = models.CharField(
        max_length=20,
        blank=True,
        help_text=(
            'International format, digits only, no "+" or spaces — '
            'e.g. 254712345678. Leave blank to hide the WhatsApp button.'
        ),
    )
    whatsapp_prefill_message = models.CharField(
        max_length=300,
        blank=True,
        default="Hello Afya Mkononi, I'd like to talk to a member of the care team.",
        help_text='Message pre-filled in WhatsApp when a patient taps the button.',
    )
    support_hours = models.CharField(
        max_length=120,
        blank=True,
        default='Mon-Fri, 8am-6pm EAT',
        help_text='Shown under the human support card.',
    )
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Site settings'
        verbose_name_plural = 'Site settings'

    def __str__(self):
        return 'Site settings'

    def save(self, *args, **kwargs):
        # Enforce the singleton: always use the same primary key.
        self.pk = self.SINGLETON_PK
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        # The singleton row should never be deleted.
        raise ValidationError('The site settings row cannot be deleted.')

    @classmethod
    def load(cls):
        """Return the singleton, creating it with defaults on first access."""
        obj, _ = cls.objects.get_or_create(pk=cls.SINGLETON_PK)
        return obj

    @property
    def has_whatsapp(self):
        return bool(self.whatsapp_number.strip())

    @property
    def wa_link(self):
        """Build a wa.me deep link, or '' when no number is configured.

        Example: https://wa.me/254712345678?text=Hello%20Afya%20Mkononi
        """
        if not self.has_whatsapp:
            return ''
        number = self.whatsapp_number.strip()
        if self.whatsapp_prefill_message:
            return f'https://wa.me/{number}?text={quote(self.whatsapp_prefill_message)}'
        return f'https://wa.me/{number}'
