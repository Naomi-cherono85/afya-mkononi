from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from apps.appointments.models import Appointment
from apps.reminders.models import Reminder

from .models import Notification

User = get_user_model()


class NotificationSignalTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user('naomi', password='pass12345')

    def test_reminder_created_emits_notification(self):
        Reminder.objects.create(
            user=self.user, patient_name='Naomi', reminder_message='Take pills',
            scheduled_for=timezone.now(),
        )
        self.assertTrue(
            Notification.objects.filter(
                user=self.user, kind=Notification.Kind.REMINDER_CREATED
            ).exists()
        )

    def test_appointment_confirmed_emits_notification_only_on_transition(self):
        appt = Appointment.objects.create(
            user=self.user, patient_name='Naomi', phone_number='1',
            preferred_date='2026-08-01', preferred_time='10:00:00', reason_for_visit='x',
        )
        # creating (pending) → no confirmed notification
        self.assertFalse(
            Notification.objects.filter(kind=Notification.Kind.APPOINTMENT_CONFIRMED).exists()
        )
        appt.status = Appointment.Status.CONFIRMED
        appt.save()
        self.assertEqual(
            Notification.objects.filter(kind=Notification.Kind.APPOINTMENT_CONFIRMED).count(), 1
        )
        # saving again while already confirmed does not duplicate
        appt.save()
        self.assertEqual(
            Notification.objects.filter(kind=Notification.Kind.APPOINTMENT_CONFIRMED).count(), 1
        )

    def test_notify_ignores_anonymous(self):
        from django.contrib.auth.models import AnonymousUser
        self.assertIsNone(
            Notification.notify(AnonymousUser(), Notification.Kind.PROFILE_UPDATED, 'x')
        )


class NotificationCentreTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user('naomi', password='pass12345')
        self.other = User.objects.create_user('other', password='pass12345')
        self.client.force_login(self.user)

    def test_list_and_unread_count_scoped(self):
        Notification.notify(self.user, Notification.Kind.PROFILE_UPDATED, 'Mine')
        Notification.notify(self.other, Notification.Kind.PROFILE_UPDATED, 'Theirs')
        resp = self.client.get(reverse('frontend:notifications'))
        self.assertContains(resp, 'Mine')
        self.assertNotContains(resp, 'Theirs')
        self.assertEqual(resp.context['unread_notifications_count'], 1)

    def test_mark_read(self):
        n = Notification.notify(self.user, Notification.Kind.PROFILE_UPDATED, 'Mine')
        resp = self.client.post(reverse('frontend:notification-read', args=[n.pk]))
        self.assertEqual(resp.status_code, 302)
        n.refresh_from_db()
        self.assertTrue(n.is_read)

    def test_mark_all_read(self):
        Notification.notify(self.user, Notification.Kind.PROFILE_UPDATED, 'a')
        Notification.notify(self.user, Notification.Kind.PROFILE_UPDATED, 'b')
        self.client.post(reverse('frontend:notification-read-all'))
        self.assertEqual(Notification.objects.filter(user=self.user, is_read=False).count(), 0)

    def test_cannot_mark_others_notification(self):
        n = Notification.notify(self.other, Notification.Kind.PROFILE_UPDATED, 'Theirs')
        resp = self.client.post(reverse('frontend:notification-read', args=[n.pk]))
        self.assertEqual(resp.status_code, 404)
