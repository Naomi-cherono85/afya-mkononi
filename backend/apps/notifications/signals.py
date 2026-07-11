"""Signal handlers that turn domain events into in-app notifications.

Kept in the notifications app so the appointments/reminders apps stay unaware of
notifications (one-way dependency). Handlers are connected from ``apps.py``.
"""
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.urls import reverse

from apps.appointments.models import Appointment
from apps.reminders.models import Reminder

from .models import Notification


@receiver(pre_save, sender=Appointment)
def _capture_previous_appointment_status(sender, instance, **kwargs):
    """Remember the pre-save status so post_save can detect a transition."""
    if instance.pk:
        instance._prev_status = (
            sender.objects.filter(pk=instance.pk)
            .values_list('status', flat=True)
            .first()
        )
    else:
        instance._prev_status = None


@receiver(post_save, sender=Appointment)
def _notify_appointment_confirmed(sender, instance, created, **kwargs):
    if created or not instance.user_id:
        return
    prev = getattr(instance, '_prev_status', None)
    if prev != Appointment.Status.CONFIRMED and instance.status == Appointment.Status.CONFIRMED:
        Notification.notify(
            instance.user,
            kind=Notification.Kind.APPOINTMENT_CONFIRMED,
            title='Appointment confirmed',
            message=f'Your appointment on {instance.preferred_date} has been confirmed.',
            url=reverse('frontend:appointment-detail', args=[instance.pk]),
        )


@receiver(post_save, sender=Reminder)
def _notify_reminder_created(sender, instance, created, **kwargs):
    if created and instance.user_id:
        Notification.notify(
            instance.user,
            kind=Notification.Kind.REMINDER_CREATED,
            title='Reminder created',
            message=instance.reminder_message[:120],
            url=reverse('frontend:reminder-list'),
        )
