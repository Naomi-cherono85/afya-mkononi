"""Keep an appointment's reminder entries in sync with its status.

When an appointment is *confirmed* we create two reminders (24h and 2h before);
when it is cancelled/completed/missed we cancel any pending ones; when it is
rescheduled we rebuild them against the new date/time. Reminders show up in the
existing Reminder module automatically.
"""
from datetime import datetime, timedelta

from django.utils import timezone
from django.utils.dateparse import parse_date, parse_time

# Hours-before-appointment for each auto reminder, with a human label.
REMINDER_OFFSETS = ((24, '24 hours'), (2, '2 hours'))


def _appointment_datetime(appointment):
    # Tolerate string date/time (e.g. an instance built with string kwargs and
    # re-saved before a DB refresh) as well as proper date/time objects.
    appt_date = appointment.preferred_date
    appt_time = appointment.preferred_time
    if isinstance(appt_date, str):
        appt_date = parse_date(appt_date)
    if isinstance(appt_time, str):
        appt_time = parse_time(appt_time)
    naive = datetime.combine(appt_date, appt_time)
    if timezone.is_naive(naive):
        return timezone.make_aware(naive, timezone.get_current_timezone())
    return naive


def _rebuild_reminders(appointment):
    from apps.reminders.models import Reminder

    # Idempotent rebuild: clear pending auto reminders, then recreate.
    appointment.reminders.filter(status=Reminder.Status.PENDING).delete()

    appt_dt = _appointment_datetime(appointment)
    now = timezone.now()
    type_label = appointment.get_appointment_type_display()
    # Format from the coerced datetime so string date/time fields are safe too.
    local_dt = timezone.localtime(appt_dt)
    when_label = f"{local_dt:%d %b %Y} at {local_dt:%I:%M %p}"

    for hours, label in REMINDER_OFFSETS:
        when = appt_dt - timedelta(hours=hours)
        if when <= now:
            continue  # never schedule a reminder in the past
        Reminder.objects.create(
            user=appointment.user,
            appointment=appointment,
            patient_name=appointment.patient_name,
            reminder_type=Reminder.ReminderType.APPOINTMENT,
            reminder_message=f'{type_label} on {when_label} — {label} to go.',
            scheduled_for=when,
        )


def sync_appointment_reminders(appointment):
    """Create / refresh / cancel reminders to match the appointment's status."""
    from apps.appointments.models import Appointment
    from apps.reminders.models import Reminder

    if not appointment.user_id:
        return

    status = appointment.status
    if status == Appointment.Status.CONFIRMED:
        _rebuild_reminders(appointment)
    elif status == Appointment.Status.RESCHEDULED:
        # Only refresh if the appointment already had reminders (i.e. it had
        # been confirmed before). A never-confirmed reschedule stays reminder-less.
        if appointment.reminders.exists():
            _rebuild_reminders(appointment)
    else:  # CANCELLED / COMPLETED / MISSED / PENDING
        appointment.reminders.filter(
            status=Reminder.Status.PENDING,
        ).update(status=Reminder.Status.CANCELLED)
