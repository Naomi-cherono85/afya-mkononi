"""Appointment slot availability.

Pure helpers (no request coupling) so they can be reused by the booking form,
the DRF serializer and the availability API — and unit-tested in isolation.

A slot is a 30-minute start time within a clinic's opening hours. It is
*unavailable* when it is in the past, on a closed day, or already at capacity
(``clinic.slot_capacity`` active appointments — per doctor when one is chosen,
otherwise across the whole practice).
"""
from datetime import datetime, time, timedelta

from django.core.exceptions import ValidationError
from django.utils import timezone

SLOT_MINUTES = 30
DEFAULT_CAPACITY = 2

# Fallback hours used only when no Clinic is configured at all.
_FALLBACK_WEEKDAY = (time(8, 0), time(17, 0))
_FALLBACK_SATURDAY = (time(8, 0), time(13, 0))


def _default_clinic():
    # Imported lazily to avoid import cycles at app-loading time.
    from apps.appointments.models import Clinic
    return Clinic.objects.filter(is_active=True).first()


def _hours_for(clinic, date):
    """(opens, closes) for the given date, or ``None`` when closed."""
    if clinic is not None:
        return clinic.hours_for_weekday(date.weekday())
    weekday = date.weekday()
    if weekday == 6:
        return None
    return _FALLBACK_SATURDAY if weekday == 5 else _FALLBACK_WEEKDAY


def slots_for_date(clinic, date):
    """List of ``datetime.time`` slot starts for the clinic on ``date``.

    Empty when the clinic is closed that day.
    """
    hours = _hours_for(clinic, date)
    if hours is None:
        return []
    opens, closes = hours
    slots = []
    cursor = datetime.combine(date, opens)
    end = datetime.combine(date, closes)
    while cursor < end:
        slots.append(cursor.time())
        cursor += timedelta(minutes=SLOT_MINUTES)
    return slots


def _capacity(clinic):
    return clinic.slot_capacity if clinic is not None else DEFAULT_CAPACITY


def _slot_counts(date, doctor=None, exclude_pk=None):
    """Map ``'HH:MM' -> active-appointment count`` for the given date."""
    from apps.appointments.models import Appointment

    qs = Appointment.objects.filter(
        preferred_date=date,
        status__in=Appointment.ACTIVE_STATUSES,
    )
    if doctor is not None:
        qs = qs.filter(doctor=doctor)
    if exclude_pk:
        qs = qs.exclude(pk=exclude_pk)

    counts = {}
    for slot_time in qs.values_list('preferred_time', flat=True):
        key = slot_time.strftime('%H:%M')
        counts[key] = counts.get(key, 0) + 1
    return counts


def _fmt_ampm(t):
    return t.strftime('%I:%M %p').lstrip('0')


def get_available_slots(date, clinic=None, doctor=None, exclude_pk=None):
    """Return ``[{value, label, available}]`` for every slot on ``date``.

    ``value`` is ``'HH:MM'`` (form value); ``label`` is a friendly ``9:30 AM``.
    """
    clinic = clinic if clinic is not None else _default_clinic()
    capacity = _capacity(clinic)
    now = timezone.localtime()
    counts = _slot_counts(date, doctor=doctor, exclude_pk=exclude_pk)

    out = []
    for slot_time in slots_for_date(clinic, date):
        key = slot_time.strftime('%H:%M')
        is_past = date < now.date() or (date == now.date() and slot_time <= now.time())
        is_full = counts.get(key, 0) >= capacity
        out.append({
            'value': key,
            'label': _fmt_ampm(slot_time),
            'available': not is_past and not is_full,
        })
    return out


def get_day_availability(start, end, clinic=None, doctor=None):
    """Per-day summary ``[{date, closed, has_slots}]`` for ``start..end``.

    Used to highlight bookable days in the date picker.
    """
    clinic = clinic if clinic is not None else _default_clinic()
    days = []
    cursor = start
    while cursor <= end:
        slots = get_available_slots(cursor, clinic=clinic, doctor=doctor)
        days.append({
            'date': cursor.isoformat(),
            'closed': len(slots) == 0,
            'has_slots': any(s['available'] for s in slots),
        })
        cursor += timedelta(days=1)
    return days


def validate_slot(date, slot_time, clinic=None, doctor=None, exclude_pk=None):
    """Raise ``ValidationError`` if the date/time cannot be booked.

    Shared by the form and the serializer so UI and API validate identically.
    """
    now = timezone.localtime()
    if date < now.date():
        raise ValidationError('Please choose a date that is not in the past.')

    clinic = clinic if clinic is not None else _default_clinic()
    if not slots_for_date(clinic, date):
        raise ValidationError('The clinic is closed on that day. Please choose another date.')

    if date == now.date() and slot_time <= now.time():
        raise ValidationError('Please choose a time later than now.')

    counts = _slot_counts(date, doctor=doctor, exclude_pk=exclude_pk)
    if counts.get(slot_time.strftime('%H:%M'), 0) >= _capacity(clinic):
        raise ValidationError('That time slot is fully booked. Please choose another time.')
