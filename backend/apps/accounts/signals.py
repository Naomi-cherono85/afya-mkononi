from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import Profile


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def ensure_profile(sender, instance, created, **kwargs):
    """Create a Profile the first time a User is saved, and keep it in sync."""
    if created:
        Profile.objects.create(user=instance)
    else:
        # Guard against users created before the profile model existed.
        Profile.objects.get_or_create(user=instance)
