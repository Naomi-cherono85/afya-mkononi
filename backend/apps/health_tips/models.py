from django.db import models


class HealthTip(models.Model):
    """An editorial health tip surfaced as the 'Health Tip of the Day'.

    Administrators manage these from Django Admin. The dashboard rotates through
    active tips deterministically (one per calendar day) via
    ``apps.health_tips.context_processors.health_tip_of_the_day``.
    """

    class Category(models.TextChoices):
        GENERAL = 'GENERAL', 'General Wellness'
        NUTRITION = 'NUTRITION', 'Nutrition'
        MENTAL_HEALTH = 'MENTAL_HEALTH', 'Mental Health'
        PREVENTION = 'PREVENTION', 'Prevention'
        MATERNAL = 'MATERNAL', 'Maternal & Child'
        CHRONIC = 'CHRONIC', 'Chronic Conditions'

    title = models.CharField(max_length=120)
    description = models.TextField(
        help_text='The body of the tip. A sentence or two works best.',
    )
    image = models.ImageField(
        upload_to='health_tips/',
        blank=True,
        help_text='Optional. A soft placeholder is shown when no image is set.',
    )
    category = models.CharField(
        max_length=20,
        choices=Category.choices,
        default=Category.GENERAL,
    )
    is_active = models.BooleanField(
        default=True,
        help_text='Only active tips appear in the daily rotation.',
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['is_active', 'created_at']),
        ]

    def __str__(self):
        return self.title
