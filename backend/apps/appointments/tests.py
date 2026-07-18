from datetime import time, timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from apps.appointments.models import Appointment, Clinic, Doctor
from apps.reminders.models import Reminder

User = get_user_model()


def next_weekday(target_weekday):
    """First future date (from tomorrow) that falls on ``target_weekday`` (Mon=0)."""
    d = timezone.localdate() + timedelta(days=1)
    while d.weekday() != target_weekday:
        d += timedelta(days=1)
    return d


class AppointmentAPITest(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user('naomi', password='pass12345')
        self.monday = next_weekday(0)

    def _payload(self, **overrides):
        data = {
            'patient_name': 'Naomi',
            'phone_number': '0712345678',
            'email': 'naomi@test.com',
            'preferred_date': self.monday.isoformat(),
            'preferred_time': '10:00:00',
            'reason_for_visit': 'Headache',
        }
        data.update(overrides)
        return data

    def test_create_appointment_requires_auth(self):
        response = self.client.post('/api/appointments/', self._payload(), format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(Appointment.objects.count(), 0)

    def test_create_appointment_assigns_owner(self):
        self.client.force_authenticate(self.user)
        response = self.client.post('/api/appointments/', self._payload(), format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Appointment.objects.get().user, self.user)

    def test_create_rejects_past_date(self):
        self.client.force_authenticate(self.user)
        past = (timezone.localdate() - timedelta(days=1)).isoformat()
        response = self.client.post('/api/appointments/', self._payload(preferred_date=past), format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_list_is_scoped_to_owner(self):
        other = User.objects.create_user('other', password='pass12345')
        Appointment.objects.create(
            user=other, patient_name='Other', phone_number='1',
            preferred_date=self.monday, preferred_time=time(9, 0), reason_for_visit='x',
        )
        mine = Appointment.objects.create(
            user=self.user, patient_name='Mine', phone_number='2',
            preferred_date=self.monday, preferred_time=time(11, 0), reason_for_visit='y',
        )
        self.client.force_authenticate(self.user)
        response = self.client.get('/api/appointments/')
        ids = [row['id'] for row in response.json()]
        self.assertEqual(ids, [mine.id])

    def test_availability_endpoint_marks_full_slots(self):
        # Capacity is 2 (seeded clinic). Two active appointments fill the 10:00 slot.
        for i in range(2):
            Appointment.objects.create(
                user=self.user, patient_name=f'P{i}', phone_number='1',
                preferred_date=self.monday, preferred_time=time(10, 0),
                reason_for_visit='x', status=Appointment.Status.CONFIRMED,
            )
        self.client.force_authenticate(self.user)
        response = self.client.get('/api/appointments/availability/', {'date': self.monday.isoformat()})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        slots = {s['value']: s['available'] for s in response.json()['slots']}
        self.assertFalse(slots['10:00'])   # full
        self.assertTrue(slots['11:00'])    # still free

    def test_availability_requires_date(self):
        self.client.force_authenticate(self.user)
        response = self.client.get('/api/appointments/availability/')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class BookingViewTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            'naomi', password='pass12345', email='naomi@test.com',
            first_name='Naomi', last_name='C',
        )
        self.user.profile.phone_number = '0712345678'
        self.user.profile.save()
        self.client.force_login(self.user)
        self.monday = next_weekday(0)

    def _form_data(self, **overrides):
        data = {
            'patient_name': 'Naomi C',
            'phone_number': '0712345678',
            'email': 'naomi@test.com',
            'appointment_type': Appointment.AppointmentType.GENERAL,
            'doctor': '',
            'clinic': '',
            'preferred_date': self.monday.isoformat(),
            'preferred_time': '10:30',
            'reason_for_visit': 'Persistent cough',
            'additional_notes': '',
        }
        data.update(overrides)
        return data

    def test_get_prefills_from_profile(self):
        response = self.client.get(reverse('frontend:appointment-book'))
        self.assertEqual(response.status_code, 200)
        form = response.context['form']
        self.assertEqual(form.initial['patient_name'], 'Naomi C')
        self.assertEqual(form.initial['email'], 'naomi@test.com')
        self.assertEqual(form.initial['phone_number'], '0712345678')

    def test_chatbot_prefill_and_source(self):
        response = self.client.get(
            reverse('frontend:appointment-book'),
            {'source': 'chatbot', 'reason': 'I have a fever', 'type': 'TELECONSULT'},
        )
        self.assertTrue(response.context['ai_suggested'])
        self.assertEqual(response.context['form'].initial['reason_for_visit'], 'I have a fever')
        self.assertEqual(response.context['form'].initial['appointment_type'], 'TELECONSULT')

    def test_booking_creates_appointment_and_redirects_to_success(self):
        response = self.client.post(reverse('frontend:appointment-book'), self._form_data())
        appt = Appointment.objects.get()
        self.assertEqual(appt.user, self.user)
        self.assertEqual(appt.source, Appointment.Source.WEB)
        self.assertRedirects(response, reverse('frontend:appointment-success', args=[appt.pk]))

    def test_booking_from_chatbot_flags_source(self):
        data = self._form_data(source='CHATBOT')
        self.client.post(reverse('frontend:appointment-book'), data)
        self.assertEqual(Appointment.objects.get().source, Appointment.Source.CHATBOT)

    def test_booking_rejects_closed_day(self):
        sunday = next_weekday(6)
        response = self.client.post(
            reverse('frontend:appointment-book'),
            self._form_data(preferred_date=sunday.isoformat()),
        )
        self.assertEqual(response.status_code, 200)  # re-rendered with errors
        self.assertEqual(Appointment.objects.count(), 0)
        self.assertTrue(response.context['form'].errors)

    def test_booking_rejects_full_slot(self):
        for i in range(2):
            Appointment.objects.create(
                user=self.user, patient_name=f'P{i}', phone_number='1',
                preferred_date=self.monday, preferred_time=time(10, 30),
                reason_for_visit='x', status=Appointment.Status.CONFIRMED,
            )
        response = self.client.post(reverse('frontend:appointment-book'), self._form_data())
        self.assertEqual(Appointment.objects.filter(reason_for_visit='Persistent cough').count(), 0)
        self.assertTrue(response.context['form'].errors)


class ManagementViewTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user('naomi', password='pass12345')
        self.client.force_login(self.user)
        self.monday = next_weekday(0)
        self.appt = Appointment.objects.create(
            user=self.user, patient_name='Naomi', phone_number='0712',
            appointment_type=Appointment.AppointmentType.GENERAL,
            preferred_date=self.monday, preferred_time=time(9, 0),
            reason_for_visit='Checkup', status=Appointment.Status.PENDING,
        )

    def test_edit_updates_fields(self):
        data = {
            'patient_name': 'Naomi Updated',
            'phone_number': '0712',
            'email': '',
            'appointment_type': Appointment.AppointmentType.FOLLOWUP,
            'doctor': '',
            'clinic': '',
            'preferred_date': self.monday.isoformat(),
            'preferred_time': '09:00',
            'reason_for_visit': 'Checkup',
            'additional_notes': '',
        }
        self.client.post(reverse('frontend:appointment-edit', args=[self.appt.pk]), data)
        self.appt.refresh_from_db()
        self.assertEqual(self.appt.patient_name, 'Naomi Updated')
        self.assertEqual(self.appt.appointment_type, Appointment.AppointmentType.FOLLOWUP)

    def test_reschedule_sets_status(self):
        new_monday = next_weekday(0) + timedelta(days=7)
        data = {
            'patient_name': 'Naomi',
            'phone_number': '0712',
            'email': '',
            'appointment_type': Appointment.AppointmentType.GENERAL,
            'doctor': '',
            'clinic': '',
            'preferred_date': new_monday.isoformat(),
            'preferred_time': '14:00',
            'reason_for_visit': 'Checkup',
            'additional_notes': '',
        }
        self.client.post(reverse('frontend:appointment-reschedule', args=[self.appt.pk]), data)
        self.appt.refresh_from_db()
        self.assertEqual(self.appt.status, Appointment.Status.RESCHEDULED)
        self.assertEqual(self.appt.preferred_date, new_monday)

    def test_cancel_sets_status(self):
        self.client.post(reverse('frontend:appointment-cancel', args=[self.appt.pk]))
        self.appt.refresh_from_db()
        self.assertEqual(self.appt.status, Appointment.Status.CANCELLED)

    def test_cannot_touch_others_appointment(self):
        other = User.objects.create_user('other', password='pass12345')
        other_appt = Appointment.objects.create(
            user=other, patient_name='X', phone_number='1',
            preferred_date=self.monday, preferred_time=time(9, 0), reason_for_visit='x',
        )
        response = self.client.get(reverse('frontend:appointment-detail', args=[other_appt.pk]))
        self.assertEqual(response.status_code, 404)

    def test_list_filters_by_status(self):
        Appointment.objects.create(
            user=self.user, patient_name='Done', phone_number='1',
            preferred_date=self.monday, preferred_time=time(15, 0),
            reason_for_visit='y', status=Appointment.Status.COMPLETED,
        )
        response = self.client.get(reverse('frontend:appointment-list'), {'status': 'COMPLETED'})
        names = [a.patient_name for a in response.context['appointments']]
        self.assertEqual(names, ['Done'])


class ReminderSyncTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user('naomi', password='pass12345')
        # Far enough out that both 24h and 2h reminders are in the future.
        self.date = next_weekday(0) + timedelta(days=7)
        self.appt = Appointment.objects.create(
            user=self.user, patient_name='Naomi', phone_number='0712',
            preferred_date=self.date, preferred_time=time(10, 0),
            reason_for_visit='Checkup', status=Appointment.Status.PENDING,
        )

    def test_no_reminders_while_pending(self):
        self.assertEqual(self.appt.reminders.count(), 0)

    def test_confirm_creates_two_reminders(self):
        self.appt.status = Appointment.Status.CONFIRMED
        self.appt.save()
        pending = self.appt.reminders.filter(status=Reminder.Status.PENDING)
        self.assertEqual(pending.count(), 2)
        self.assertTrue(all(r.reminder_type == Reminder.ReminderType.APPOINTMENT for r in pending))

    def test_cancel_cancels_reminders(self):
        self.appt.status = Appointment.Status.CONFIRMED
        self.appt.save()
        self.appt.status = Appointment.Status.CANCELLED
        self.appt.save()
        self.assertEqual(self.appt.reminders.filter(status=Reminder.Status.PENDING).count(), 0)
        self.assertEqual(self.appt.reminders.filter(status=Reminder.Status.CANCELLED).count(), 2)

    def test_reschedule_refreshes_reminders(self):
        self.appt.status = Appointment.Status.CONFIRMED
        self.appt.save()
        original = sorted(self.appt.reminders.values_list('scheduled_for', flat=True))
        # Move the appointment a day later and reschedule.
        self.appt.preferred_date = self.date + timedelta(days=1)
        self.appt.status = Appointment.Status.RESCHEDULED
        self.appt.save()
        refreshed = sorted(self.appt.reminders.filter(status=Reminder.Status.PENDING).values_list('scheduled_for', flat=True))
        self.assertEqual(len(refreshed), 2)
        self.assertNotEqual(original, refreshed)


class ProviderModelTest(TestCase):
    def test_seed_data_present(self):
        self.assertTrue(Clinic.objects.filter(is_active=True).exists())
        self.assertTrue(Doctor.objects.filter(is_active=True).exists())

    def test_reference_property(self):
        appt = Appointment.objects.create(
            patient_name='N', phone_number='1',
            preferred_date=next_weekday(0), preferred_time=time(9, 0), reason_for_visit='x',
        )
        self.assertEqual(appt.reference, f'AFYA-{appt.pk:05d}')
