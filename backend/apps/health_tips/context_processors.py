from django.utils import timezone

from .models import HealthTip


def health_tip_of_the_day(request):
    """Expose health tips to every template.

    ``health_tips`` is the full list of active tips (ordered), used to drive the
    dashboard carousel. ``health_tip`` is a deterministic 'tip of the day' chosen
    from that list based on the day of the year, so the featured tip is stable for
    the whole day but rotates across days. Both are empty/``None`` when no active
    tips exist (templates render an empty state).
    """
    tips = list(HealthTip.objects.filter(is_active=True).order_by('id'))
    if not tips:
        return {'health_tips': [], 'health_tip': None}

    day_index = timezone.localdate().timetuple().tm_yday
    featured_index = day_index % len(tips)

    # Put the featured tip first so the carousel opens on it, preserving the
    # rest of the rotation order behind it.
    ordered = tips[featured_index:] + tips[:featured_index]
    return {'health_tips': ordered, 'health_tip': ordered[0]}
