from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from .models import Article

User = get_user_model()


class HealthLibraryTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user('naomi', password='pass12345')
        self.client.force_login(self.user)

    def test_seed_articles_present(self):
        # The 0002 data migration should have created starter content.
        self.assertGreaterEqual(Article.objects.count(), 8)
        self.assertTrue(Article.objects.filter(category='MALARIA').exists())

    def test_list_and_category_filter(self):
        resp = self.client.get(reverse('frontend:library'), {'category': 'MALARIA'})
        self.assertEqual(resp.status_code, 200)
        for a in resp.context['articles']:
            self.assertEqual(a.category, 'MALARIA')

    def test_search(self):
        resp = self.client.get(reverse('frontend:library'), {'q': 'mosquito'})
        self.assertContains(resp, 'Preventing Mosquito Bites')

    def test_detail(self):
        article = Article.objects.first()
        resp = self.client.get(article.get_absolute_url())
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, article.title)

    def test_unpublished_hidden(self):
        art = Article.objects.create(
            title='Draft article', slug='draft-article', category='NUTRITION',
            summary='x', content='y', is_published=False,
        )
        # not in listing
        resp = self.client.get(reverse('frontend:library'))
        self.assertNotContains(resp, 'Draft article')
        # detail 404s
        resp = self.client.get(reverse('frontend:library-article', args=[art.slug]))
        self.assertEqual(resp.status_code, 404)

    def test_login_required(self):
        self.client.logout()
        resp = self.client.get(reverse('frontend:library'))
        self.assertEqual(resp.status_code, 302)
