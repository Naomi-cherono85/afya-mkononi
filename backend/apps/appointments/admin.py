from django.contrib import admin

from .models import Appointment


@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    list_display = [
        'patient_name',
        'user',
        'phone_number',
        'preferred_date',
        'preferred_time',
        'status',
        'created_at',
    ]
    list_filter = ['status', 'preferred_date', 'created_at']
    search_fields = ['patient_name', 'phone_number', 'reason_for_visit', 'user__username', 'user__email']
    list_select_related = ['user']
    date_hierarchy = 'preferred_date'
    readonly_fields = ['created_at', 'updated_at']
    actions = ['mark_confirmed', 'mark_completed', 'mark_cancelled']

    @admin.action(description='Mark selected appointments as confirmed')
    def mark_confirmed(self, request, queryset):
        # Save one-by-one so the confirmation-notification signal fires per row.
        for appt in queryset.exclude(status=Appointment.Status.CONFIRMED):
            appt.status = Appointment.Status.CONFIRMED
            appt.save(update_fields=['status', 'updated_at'])

    @admin.action(description='Mark selected appointments as completed')
    def mark_completed(self, request, queryset):
        queryset.update(status=Appointment.Status.COMPLETED)

    @admin.action(description='Mark selected appointments as cancelled')
    def mark_cancelled(self, request, queryset):
        queryset.update(status=Appointment.Status.CANCELLED)
