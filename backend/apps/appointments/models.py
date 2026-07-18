from datetime import time

from django.conf import settings
from django.db import models


class Clinic(models.Model):
    """A physical clinic a patient can request an appointment at.

    Holds the opening hours (used to generate bookable time slots) and a
    per-slot capacity (used to work out when a slot is "fully booked").
    """

    name = models.CharField(max_length=200)
    address = models.CharField(max_length=255, blank=True)
    phone = models.CharField(max_length=20, blank=True)

    # Opening hours. Sundays are closed unless ``open_sunday`` is set.
    opens_weekday = models.TimeField(default=time(8, 0))
    closes_weekday = models.TimeField(default=time(17, 0))
    opens_saturday = models.TimeField(default=time(8, 0))
    closes_saturday = models.TimeField(default=time(13, 0))
    open_sunday = models.BooleanField(default=False)

    slot_capacity = models.PositiveSmallIntegerField(
        default=2,
        help_text='Maximum appointments allowed in a single 30-minute slot.',
    )
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name

    def hours_for_weekday(self, weekday):
        """Return ``(opens, closes)`` for a Python weekday (Mon=0 … Sun=6).

        Returns ``None`` when the clinic is closed that day.
        """
        if weekday == 6:  # Sunday
            if not self.open_sunday:
                return None
            return (self.opens_weekday, self.closes_weekday)
        if weekday == 5:  # Saturday
            return (self.opens_saturday, self.closes_saturday)
        return (self.opens_weekday, self.closes_weekday)


class Doctor(models.Model):
    """A clinician a patient can optionally request."""

    name = models.CharField(max_length=200)
    specialty = models.CharField(max_length=120, blank=True)
    clinic = models.ForeignKey(
        Clinic,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='doctors',
    )
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return f"{self.name} · {self.specialty}" if self.specialty else self.name


class Appointment(models.Model):
    class Status(models.TextChoices):
        PENDING = 'PENDING', 'Pending'
        CONFIRMED = 'CONFIRMED', 'Confirmed'
        RESCHEDULED = 'RESCHEDULED', 'Rescheduled'
        COMPLETED = 'COMPLETED', 'Completed'
        CANCELLED = 'CANCELLED', 'Cancelled'
        MISSED = 'MISSED', 'Missed'

    class AppointmentType(models.TextChoices):
        GENERAL = 'GENERAL', 'General Consultation'
        FOLLOWUP = 'FOLLOWUP', 'Follow-up'
        SPECIALIST = 'SPECIALIST', 'Specialist'
        VACCINATION = 'VACCINATION', 'Vaccination'
        LAB = 'LAB', 'Laboratory Test'
        TELECONSULT = 'TELECONSULT', 'Teleconsultation'

    class Source(models.TextChoices):
        WEB = 'WEB', 'Web'
        CHATBOT = 'CHATBOT', 'Chatbot'

    # Statuses that still occupy a slot (used for capacity / availability).
    ACTIVE_STATUSES = ('PENDING', 'CONFIRMED', 'RESCHEDULED')

    # Owner of the appointment. Nullable so pre-isolation rows survive the
    # migration; they simply become invisible (no user ever matches NULL).
    # New appointments always get an owner (set server-side in the view).
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='appointments',
    )
    patient_name = models.CharField(max_length=200)
    phone_number = models.CharField(max_length=20)
    email = models.EmailField(blank=True, null=True)

    appointment_type = models.CharField(
        max_length=20,
        choices=AppointmentType.choices,
        default=AppointmentType.GENERAL,
    )
    doctor = models.ForeignKey(
        Doctor,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='appointments',
    )
    clinic = models.ForeignKey(
        Clinic,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='appointments',
    )

    preferred_date = models.DateField()
    preferred_time = models.TimeField()
    reason_for_visit = models.TextField()
    additional_notes = models.TextField(blank=True)

    source = models.CharField(
        max_length=20,
        choices=Source.choices,
        default=Source.WEB,
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status', 'preferred_date']),
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['preferred_date', 'preferred_time']),
        ]

    def __str__(self):
        return f"{self.patient_name} — {self.preferred_date} {self.preferred_time} ({self.status})"

    @property
    def reference(self):
        """Human-friendly booking reference, e.g. ``AFYA-00042``."""
        return f"AFYA-{self.pk:05d}" if self.pk else "AFYA-—"
