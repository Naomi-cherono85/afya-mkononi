from django.test import RequestFactory, TestCase

from .context_processors import health_tip_of_the_day
from .models import HealthTip


class HealthTipModelTests(TestCase):
    def test_str_is_title(self):
        tip = HealthTip.objects.create(title='Stay Hydrated', content='Drink water.')
        self.assertEqual(str(tip), 'Stay Hydrated')

    def test_image_is_optional(self):
        tip = HealthTip.objects.create(title='No image', content='Body.')
        self.assertFalse(tip.image)


class HealthTipContextProcessorTests(TestCase):
    def setUp(self):
        self.request = RequestFactory().get('/')
        # Start from a clean slate; the 0003 data migration seeds tips into the
        # test DB, which would otherwise skew these counts.
        HealthTip.objects.all().delete()

    def test_empty_state_when_no_active_tips(self):
        HealthTip.objects.create(title='Inactive', content='Body.', is_active=False)
        ctx = health_tip_of_the_day(self.request)
        self.assertEqual(ctx['health_tips'], [])
        self.assertIsNone(ctx['health_tip'])

    def test_returns_active_tips_with_featured_first(self):
        for i in range(3):
            HealthTip.objects.create(title=f'Tip {i}', content='Body.')
        ctx = health_tip_of_the_day(self.request)
        self.assertEqual(len(ctx['health_tips']), 3)
        self.assertEqual(ctx['health_tip'], ctx['health_tips'][0])

    def test_excludes_inactive_tips(self):
        HealthTip.objects.create(title='Active', content='Body.')
        HealthTip.objects.create(title='Inactive', content='Body.', is_active=False)
        ctx = health_tip_of_the_day(self.request)
        self.assertEqual(len(ctx['health_tips']), 1)
        self.assertEqual(ctx['health_tips'][0].title, 'Active')
