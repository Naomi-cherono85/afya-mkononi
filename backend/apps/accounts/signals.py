from django.conf import settings
from django.contrib.auth.signals import user_logged_in
from django.db.models.signals import post_save
from django.dispatch import receiver

from apps.core.greetings import pick_greeting

from .models import Profile


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def ensure_profile(sender, instance, created, **kwargs):
    """Create a Profile the first time a User is saved, and keep it in sync."""
    if created:
        Profile.objects.create(user=instance)
    else:
        # Guard against users created before the profile model existed.
        Profile.objects.get_or_create(user=instance)


@receiver(user_logged_in)
def rotate_login_greeting(sender, request, user, **kwargs):
    """Pick a fresh multilingual greeting on each login / account creation.

    Stored in the session so it stays put for the visit and only changes the
    next time the user signs in. Excludes the previous one so it always rotates.
    """
    if request is None:
        return
    request.session['greeting'] = pick_greeting(exclude=request.session.get('greeting'))
