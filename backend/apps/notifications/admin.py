from django.contrib import admin

from .models import Notification


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('title', 'user', 'kind', 'is_read', 'created_at')
    list_filter = ('kind', 'is_read', 'created_at')
    search_fields = ('title', 'message', 'user__username', 'user__email')
    list_select_related = ('user',)
    readonly_fields = ('created_at',)
    date_hierarchy = 'created_at'
