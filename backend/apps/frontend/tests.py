from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from apps.appointments.models import Appointment
from apps.reminders.models import Reminder

User = get_user_model()


class AppointmentManagementTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user('naomi', password='pass12345')
        self.other = User.objects.create_user('other', password='pass12345')
        self.client.force_login(self.user)
        self.appt = Appointment.objects.create(
            user=self.user, patient_name='Naomi', phone_number='0700',
            preferred_date='2026-08-01', preferred_time='10:00:00',
            reason_for_visit='Check-up',
        )

    def test_list_shows_only_own(self):
        # The redesigned list renders a table of rows linking to each detail
        # page, so we assert on the presence/absence of those links.
        other_appt = Appointment.objects.create(
            user=self.other, patient_name='Someone else', phone_number='1',
            preferred_date='2026-08-02', preferred_time='11:00:00', reason_for_visit='x',
        )
        resp = self.client.get(reverse('frontend:appointment-list'))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, reverse('frontend:appointment-detail', args=[self.appt.pk]))
        self.assertNotContains(resp, reverse('frontend:appointment-detail', args=[other_appt.pk]))

    def test_search_filters(self):
        match = Appointment.objects.create(
            user=self.user, patient_name='Naomi', phone_number='0700',
            preferred_date='2026-08-03', preferred_time='09:00:00', reason_for_visit='Malaria test',
        )
        resp = self.client.get(reverse('frontend:appointment-list'), {'q': 'malaria'})
        self.assertContains(resp, reverse('frontend:appointment-detail', args=[match.pk]))
        self.assertNotContains(resp, reverse('frontend:appointment-detail', args=[self.appt.pk]))

    def test_detail_blocks_other_users_appointment(self):
        other_appt = Appointment.objects.create(
            user=self.other, patient_name='Other', phone_number='1',
            preferred_date='2026-08-02', preferred_time='11:00:00', reason_for_visit='x',
        )
        resp = self.client.get(reverse('frontend:appointment-detail', args=[other_appt.pk]))
        self.assertEqual(resp.status_code, 404)

    def test_edit_reschedule(self):
        resp = self.client.post(reverse('frontend:appointment-edit', args=[self.appt.pk]), {
            'patient_name': 'Naomi', 'phone_number': '0700', 'email': '',
            'appointment_type': Appointment.AppointmentType.GENERAL,
            'doctor': '', 'clinic': '',
            'preferred_date': '2026-09-15', 'preferred_time': '14:30:00',
            'reason_for_visit': 'Check-up', 'additional_notes': '',
        })
        self.assertRedirects(resp, reverse('frontend:appointment-detail', args=[self.appt.pk]))
        self.appt.refresh_from_db()
        self.assertEqual(str(self.appt.preferred_date), '2026-09-15')

    def test_cancel_sets_status(self):
        resp = self.client.post(reverse('frontend:appointment-cancel', args=[self.appt.pk]))
        self.assertRedirects(resp, reverse('frontend:appointment-detail', args=[self.appt.pk]))
        self.appt.refresh_from_db()
        self.assertEqual(self.appt.status, Appointment.Status.CANCELLED)

    def test_cancel_requires_post(self):
        resp = self.client.get(reverse('frontend:appointment-cancel', args=[self.appt.pk]))
        self.assertEqual(resp.status_code, 405)

    def test_login_required(self):
        self.client.logout()
        resp = self.client.get(reverse('frontend:appointment-list'))
        self.assertEqual(resp.status_code, 302)
        self.assertIn('/accounts/login/', resp.url)


class DashboardTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user('naomi', password='pass12345')
        self.other = User.objects.create_user('other', password='pass12345')
        self.client.force_login(self.user)

    def test_quick_stats_scoped_to_user(self):
        Appointment.objects.create(
            user=self.user, patient_name='Naomi', phone_number='1',
            preferred_date=timezone.localdate() + timezone.timedelta(days=3),
            preferred_time='10:00:00', reason_for_visit='x',
        )
        Reminder.objects.create(
            user=self.user, patient_name='Naomi', reminder_message='pills',
            scheduled_for=timezone.now() + timezone.timedelta(days=1),
        )
        # other user's data must not count
        Appointment.objects.create(
            user=self.other, patient_name='Other', phone_number='1',
            preferred_date=timezone.localdate() + timezone.timedelta(days=3),
            preferred_time='10:00:00', reason_for_visit='y',
        )
        resp = self.client.get(reverse('frontend:dashboard'))
        self.assertEqual(resp.status_code, 200)
        stats = resp.context['quick_stats']
        self.assertEqual(stats['upcoming_appointments'], 1)
        self.assertEqual(stats['pending_reminders'], 1)

    def test_next_reminder_is_soonest_future(self):
        Reminder.objects.create(
            user=self.user, patient_name='Naomi', reminder_message='later',
            scheduled_for=timezone.now() + timezone.timedelta(days=5),
        )
        soon = Reminder.objects.create(
            user=self.user, patient_name='Naomi', reminder_message='soon',
            scheduled_for=timezone.now() + timezone.timedelta(hours=2),
        )
        resp = self.client.get(reverse('frontend:dashboard'))
        self.assertEqual(resp.context['next_reminder'].pk, soon.pk)


class SearchTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user('naomi', password='pass12345')
        self.other = User.objects.create_user('other', password='pass12345')
        self.client.force_login(self.user)

    def test_results_match_and_are_scoped(self):
        Appointment.objects.create(
            user=self.user, patient_name='Naomi', phone_number='1',
            preferred_date='2026-08-01', preferred_time='10:00:00',
            reason_for_visit='Malaria screening',
        )
        Appointment.objects.create(
            user=self.other, patient_name='Other', phone_number='1',
            preferred_date='2026-08-01', preferred_time='10:00:00',
            reason_for_visit='Malaria for other user',
        )
        resp = self.client.get(reverse('frontend:search-results'), {'q': 'malaria'})
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        titles = [a['title'] for a in data['appointments']]
        self.assertEqual(titles, ['Malaria screening'])

    def test_empty_query_returns_nothing(self):
        resp = self.client.get(reverse('frontend:search-results'), {'q': ''})
        data = resp.json()
        self.assertEqual(data['appointments'], [])
        self.assertEqual(data['reminders'], [])
        self.assertEqual(data['conversations'], [])

    def test_search_page_requires_login(self):
        self.client.logout()
        resp = self.client.get(reverse('frontend:search'))
        self.assertEqual(resp.status_code, 302)


class ReminderManagementTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user('naomi', password='pass12345')
        self.other = User.objects.create_user('other', password='pass12345')
        self.client.force_login(self.user)
        self.reminder = Reminder.objects.create(
            user=self.user, patient_name='Naomi', reminder_message='Take pills',
            scheduled_for=timezone.now() + timezone.timedelta(days=2),
        )

    def test_upcoming_and_completed_tabs(self):
        done = Reminder.objects.create(
            user=self.user, patient_name='Naomi', reminder_message='Old one',
            scheduled_for=timezone.now(), status=Reminder.Status.COMPLETED,
        )
        up = self.client.get(reverse('frontend:reminder-list'))
        self.assertContains(up, 'Take pills')
        self.assertNotContains(up, 'Old one')
        comp = self.client.get(reverse('frontend:reminder-list'), {'tab': 'completed'})
        self.assertContains(comp, 'Old one')
        self.assertNotContains(comp, 'Take pills')

    def test_list_scoped_to_owner(self):
        Reminder.objects.create(
            user=self.other, patient_name='Other', reminder_message='Secret reminder',
            scheduled_for=timezone.now() + timezone.timedelta(days=1),
        )
        resp = self.client.get(reverse('frontend:reminder-list'))
        self.assertNotContains(resp, 'Secret reminder')

    def test_complete(self):
        resp = self.client.post(reverse('frontend:reminder-complete', args=[self.reminder.pk]))
        self.assertRedirects(resp, reverse('frontend:reminder-list'))
        self.reminder.refresh_from_db()
        self.assertEqual(self.reminder.status, Reminder.Status.COMPLETED)
        self.assertIsNotNone(self.reminder.completed_at)

    def test_snooze_pushes_a_day(self):
        original = self.reminder.scheduled_for
        resp = self.client.post(reverse('frontend:reminder-snooze', args=[self.reminder.pk]))
        self.assertRedirects(resp, reverse('frontend:reminder-list'))
        self.reminder.refresh_from_db()
        self.assertEqual((self.reminder.scheduled_for - original).days, 1)

    def test_edit(self):
        resp = self.client.post(reverse('frontend:reminder-edit', args=[self.reminder.pk]), {
            'reminder_type': 'MEDICATION', 'reminder_message': 'Updated message',
            'scheduled_for': '2026-09-01T08:30',
        })
        self.assertRedirects(resp, reverse('frontend:reminder-list'))
        self.reminder.refresh_from_db()
        self.assertEqual(self.reminder.reminder_message, 'Updated message')

    def test_delete(self):
        resp = self.client.post(reverse('frontend:reminder-delete', args=[self.reminder.pk]))
        self.assertRedirects(resp, reverse('frontend:reminder-list'))
        self.assertFalse(Reminder.objects.filter(pk=self.reminder.pk).exists())

    def test_cannot_delete_others_reminder(self):
        other_r = Reminder.objects.create(
            user=self.other, patient_name='Other', reminder_message='x',
            scheduled_for=timezone.now(),
        )
        resp = self.client.post(reverse('frontend:reminder-delete', args=[other_r.pk]))
        self.assertEqual(resp.status_code, 404)
        self.assertTrue(Reminder.objects.filter(pk=other_r.pk).exists())
