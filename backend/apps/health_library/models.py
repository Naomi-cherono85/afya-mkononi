from django.db import models
from django.urls import reverse


class Article(models.Model):
    """A searchable, admin-managed health education article.

    Informational only — content must never diagnose or prescribe (mirrors the
    chatbot's safety boundaries). Mirrors the conventions of ``HealthTip``.
    """

    class Category(models.TextChoices):
        MALARIA = 'MALARIA', 'Malaria'
        DIABETES = 'DIABETES', 'Diabetes'
        HYPERTENSION = 'HYPERTENSION', 'Hypertension'
        PREGNANCY = 'PREGNANCY', 'Pregnancy'
        NUTRITION = 'NUTRITION', 'Nutrition'
        MENTAL_HEALTH = 'MENTAL_HEALTH', 'Mental Health'
        CHILD_HEALTH = 'CHILD_HEALTH', 'Child Health'
        VACCINATION = 'VACCINATION', 'Vaccination'

    title = models.CharField(max_length=160)
    slug = models.SlugField(max_length=180, unique=True)
    category = models.CharField(max_length=20, choices=Category.choices)
    summary = models.CharField(max_length=300, help_text='One or two sentences shown in listings.')
    content = models.TextField(help_text='Full article body. Informational only — no diagnosis or prescriptions.')
    image = models.ImageField(upload_to='health_library/', blank=True, null=True)
    is_published = models.BooleanField(default=True, help_text='Only published articles appear in the library.')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['title']
        indexes = [
            models.Index(fields=['category', 'is_published']),
        ]

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse('frontend:library-article', args=[self.slug])
