from django.db import models


class Reminder(models.Model):
    class ReminderType(models.TextChoices):
        MEDICATION = 'MEDICATION', 'Medication'
        APPOINTMENT = 'APPOINTMENT', 'Appointment'
        FOLLOWUP = 'FOLLOWUP', 'Follow-up'
        OTHER = 'OTHER', 'Other'

    class Status(models.TextChoices):
        PENDING = 'PENDING', 'Pending'
        SENT = 'SENT', 'Sent'
        CANCELLED = 'CANCELLED', 'Cancelled'

    patient_name = models.CharField(max_length=200)
    reminder_type = models.CharField(
        max_length=20,
        choices=ReminderType.choices,
        default=ReminderType.OTHER,
    )
    reminder_message = models.TextField()
    scheduled_for = models.DateTimeField()
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
    )
    sent_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status', 'scheduled_for']),
        ]

    def __str__(self):
        return f"{self.patient_name} — {self.reminder_type} at {self.scheduled_for:%Y-%m-%d %H:%M} ({self.status})"
