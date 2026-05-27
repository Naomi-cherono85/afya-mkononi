from django.db import models


class Appointment(models.Model):
    class Status(models.TextChoices):
        PENDING = 'PENDING', 'Pending'
        CONFIRMED = 'CONFIRMED', 'Confirmed'
        CANCELLED = 'CANCELLED', 'Cancelled'
        COMPLETED = 'COMPLETED', 'Completed'

    patient_name = models.CharField(max_length=200)
    phone_number = models.CharField(max_length=20)
    email = models.EmailField(blank=True, null=True)
    preferred_date = models.DateField()
    preferred_time = models.TimeField()
    reason_for_visit = models.TextField()
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
        ]

    def __str__(self):
        return f"{self.patient_name} — {self.preferred_date} {self.preferred_time} ({self.status})"
