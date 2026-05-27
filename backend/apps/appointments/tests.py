from rest_framework import status
from rest_framework.test import APITestCase
from apps.appointments.models import Appointment


class AppointmentAPITest(APITestCase):
    def test_create_appointment(self):
        data = {
            "patient_name": "Naomi",
            "phone_number": "0712345678",
            "email": "naomi@test.com",
            "preferred_date": "2026-06-01",
            "preferred_time": "10:00:00",
            "reason_for_visit": "Headache"
        }

        response = self.client.post("/api/appointments/", data, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Appointment.objects.count(), 1)

# Create your tests here.
