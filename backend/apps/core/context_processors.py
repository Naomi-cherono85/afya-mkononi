from .models import SiteSettings


def site_settings(request):
    """Expose the singleton ``SiteSettings`` to every template as ``site_settings``.

    Used by the human-support / WhatsApp card and any other site-wide chrome.
    """
    return {'site_settings': SiteSettings.load()}
