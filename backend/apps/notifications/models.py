from django.conf import settings
from django.db import models


class Notification(models.Model):
    """A lightweight, per-user in-app notification shown in the bell/centre."""

    class Kind(models.TextChoices):
        APPOINTMENT_CONFIRMED = 'APPOINTMENT_CONFIRMED', 'Appointment confirmed'
        REMINDER_CREATED = 'REMINDER_CREATED', 'New reminder created'
        REMINDER_COMPLETED = 'REMINDER_COMPLETED', 'Reminder completed'
        PROFILE_UPDATED = 'PROFILE_UPDATED', 'Profile updated'

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='notifications',
    )
    kind = models.CharField(max_length=32, choices=Kind.choices)
    title = models.CharField(max_length=120)
    message = models.CharField(max_length=300, blank=True)
    url = models.CharField(max_length=300, blank=True, help_text='Optional link opened when the notification is clicked.')
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'is_read', '-created_at']),
        ]

    def __str__(self):
        return f'{self.get_kind_display()} → {self.user.get_username()}'

    @classmethod
    def notify(cls, user, kind, title, message='', url=''):
        """Create a notification for ``user``. No-op for anonymous/None users."""
        if user is None or not getattr(user, 'is_authenticated', False):
            return None
        return cls.objects.create(
            user=user, kind=kind, title=title, message=message, url=url,
        )
