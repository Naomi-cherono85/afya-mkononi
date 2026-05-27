from django.contrib import admin

from .models import Reminder


@admin.register(Reminder)
class ReminderAdmin(admin.ModelAdmin):
    list_display = [
        'patient_name',
        'reminder_type',
        'scheduled_for',
        'status',
        'sent_at',
        'created_at',
    ]
    list_filter = ['status', 'reminder_type', 'scheduled_for']
    search_fields = ['patient_name', 'reminder_message']
    readonly_fields = ['created_at']
