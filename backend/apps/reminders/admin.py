from django.utils import timezone

from django.contrib import admin

from .models import Reminder


@admin.register(Reminder)
class ReminderAdmin(admin.ModelAdmin):
    list_display = [
        'patient_name',
        'user',
        'reminder_type',
        'scheduled_for',
        'status',
        'completed_at',
        'created_at',
    ]
    list_filter = ['status', 'reminder_type', 'scheduled_for', 'created_at']
    search_fields = ['patient_name', 'reminder_message', 'user__username', 'user__email']
    list_select_related = ['user']
    date_hierarchy = 'scheduled_for'
    readonly_fields = ['created_at']
    actions = ['mark_completed', 'mark_cancelled']

    @admin.action(description='Mark selected reminders as completed')
    def mark_completed(self, request, queryset):
        queryset.update(status=Reminder.Status.COMPLETED, completed_at=timezone.now())

    @admin.action(description='Mark selected reminders as cancelled')
    def mark_cancelled(self, request, queryset):
        queryset.update(status=Reminder.Status.CANCELLED)
