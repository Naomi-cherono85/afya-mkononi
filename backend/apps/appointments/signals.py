"""Auto-manage appointment reminders on status / schedule changes.

Connected from ``AppointmentsConfig.ready()``. Kept separate from the
notifications app's Appointment signals (both can coexist on the same model).
"""
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver

from .models import Appointment
from .services.reminders import sync_appointment_reminders


@receiver(pre_save, sender=Appointment)
def _capture_previous_appointment(sender, instance, **kwargs):
    """Snapshot status + schedule so post_save can detect a change."""
    if instance.pk:
        instance._prev_appt = (
            sender.objects
            .filter(pk=instance.pk)
            .values('status', 'preferred_date', 'preferred_time')
            .first()
        )
    else:
        instance._prev_appt = None


@receiver(post_save, sender=Appointment)
def _sync_reminders_on_change(sender, instance, created, **kwargs):
    prev = getattr(instance, '_prev_appt', None)
    status_changed = created or not prev or prev['status'] != instance.status
    schedule_changed = bool(prev) and (
        prev['preferred_date'] != instance.preferred_date
        or prev['preferred_time'] != instance.preferred_time
    )
    if status_changed or schedule_changed:
        sync_appointment_reminders(instance)
