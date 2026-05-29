from django.utils import timezone

from .models import HealthTip


def health_tip_of_the_day(request):
    """Expose a deterministic 'tip of the day' to every template as ``health_tip``.

    Picks one active tip based on the day of the year, so the tip is stable for
    the whole day but rotates across days. Returns ``None`` when no active tips
    exist (templates render an empty state).
    """
    tips = list(HealthTip.objects.filter(is_active=True).order_by('id'))
    if not tips:
        return {'health_tip': None}

    day_index = timezone.localdate().timetuple().tm_yday
    tip = tips[day_index % len(tips)]
    return {'health_tip': tip}
