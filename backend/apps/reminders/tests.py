from rest_framework import status
from rest_framework.test import APITestCase
from apps.reminders.models import Reminder


class ReminderAPITest(APITestCase):
    def test_create_reminder(self):
        data = {
            "patient_name": "Naomi",
            "reminder_type": "MEDICATION",
            "reminder_message": "Take your medication",
            "scheduled_for": "2026-06-05T10:30:00",
            "status": "PENDING"
        }

        response = self.client.post("/api/reminders/", data, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Reminder.objects.count(), 1)

# Create your tests here.
