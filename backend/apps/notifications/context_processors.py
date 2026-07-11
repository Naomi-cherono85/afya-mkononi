from .models import Notification


def notifications(request):
    """Expose the unread count and a few recent notifications to every template.

    Powers the nav bell badge and any dropdown/preview. Cheap: one count and a
    small slice, both indexed by ``(user, is_read, -created_at)``.
    """
    user = getattr(request, 'user', None)
    if user is None or not user.is_authenticated:
        return {'unread_notifications_count': 0, 'recent_notifications': []}

    qs = Notification.objects.filter(user=user)
    return {
        'unread_notifications_count': qs.filter(is_read=False).count(),
        'recent_notifications': list(qs[:5]),
    }
