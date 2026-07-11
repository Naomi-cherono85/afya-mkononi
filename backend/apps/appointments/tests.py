from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APITestCase

from apps.appointments.models import Appointment

User = get_user_model()


class AppointmentAPITest(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user('naomi', password='pass12345')

    def test_create_appointment_requires_auth(self):
        data = {
            "patient_name": "Naomi",
            "phone_number": "0712345678",
            "email": "naomi@test.com",
            "preferred_date": "2026-06-01",
            "preferred_time": "10:00:00",
            "reason_for_visit": "Headache",
        }
        response = self.client.post("/api/appointments/", data, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(Appointment.objects.count(), 0)

    def test_create_appointment_assigns_owner(self):
        self.client.force_authenticate(self.user)
        data = {
            "patient_name": "Naomi",
            "phone_number": "0712345678",
            "email": "naomi@test.com",
            "preferred_date": "2026-06-01",
            "preferred_time": "10:00:00",
            "reason_for_visit": "Headache",
        }
        response = self.client.post("/api/appointments/", data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Appointment.objects.count(), 1)
        # Owner is set server-side even though the client never sent it.
        self.assertEqual(Appointment.objects.get().user, self.user)

    def test_list_is_scoped_to_owner(self):
        """A user must never see another user's appointments."""
        other = User.objects.create_user('other', password='pass12345')
        Appointment.objects.create(
            user=other, patient_name='Other', phone_number='1',
            preferred_date='2026-06-01', preferred_time='10:00:00',
            reason_for_visit='x',
        )
        mine = Appointment.objects.create(
            user=self.user, patient_name='Mine', phone_number='2',
            preferred_date='2026-06-02', preferred_time='11:00:00',
            reason_for_visit='y',
        )
        self.client.force_authenticate(self.user)
        response = self.client.get("/api/appointments/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        ids = [row['id'] for row in response.json()]
        self.assertEqual(ids, [mine.id])
