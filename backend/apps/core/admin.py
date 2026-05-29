from django.contrib import admin

from .models import SiteSettings


@admin.register(SiteSettings)
class SiteSettingsAdmin(admin.ModelAdmin):
    """Admin for the singleton site settings row.

    Hides the "add" button once the row exists and never offers deletion, so
    administrators only ever edit the one configuration object.
    """

    fieldsets = (
        ('Human support', {
            'fields': (
                'care_team_name',
                'whatsapp_number',
                'whatsapp_prefill_message',
                'support_hours',
            ),
        }),
    )
    readonly_fields = ('updated_at',)

    def has_add_permission(self, request):
        return not SiteSettings.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False
