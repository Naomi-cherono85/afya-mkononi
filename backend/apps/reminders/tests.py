from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APITestCase

from apps.reminders.models import Reminder

User = get_user_model()


class ReminderAPITest(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user('naomi', password='pass12345')

    def test_create_reminder_requires_auth(self):
        data = {
            "patient_name": "Naomi",
            "reminder_type": "MEDICATION",
            "reminder_message": "Take your medication",
            "scheduled_for": "2026-06-05T10:30:00",
        }
        response = self.client.post("/api/reminders/", data, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(Reminder.objects.count(), 0)

    def test_create_reminder_assigns_owner(self):
        self.client.force_authenticate(self.user)
        data = {
            "patient_name": "Naomi",
            "reminder_type": "MEDICATION",
            "reminder_message": "Take your medication",
            "scheduled_for": "2026-06-05T10:30:00",
        }
        response = self.client.post("/api/reminders/", data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Reminder.objects.count(), 1)
        self.assertEqual(Reminder.objects.get().user, self.user)

    def test_list_is_scoped_to_owner(self):
        """A user must never see another user's reminders."""
        other = User.objects.create_user('other', password='pass12345')
        Reminder.objects.create(
            user=other, patient_name='Other', reminder_message='x',
            scheduled_for='2026-06-05T10:30:00',
        )
        mine = Reminder.objects.create(
            user=self.user, patient_name='Mine', reminder_message='y',
            scheduled_for='2026-06-06T10:30:00',
        )
        self.client.force_authenticate(self.user)
        response = self.client.get("/api/reminders/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        ids = [row['id'] for row in response.json()]
        self.assertEqual(ids, [mine.id])
