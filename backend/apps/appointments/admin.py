from django.contrib import admin

from .models import Appointment, Clinic, Doctor


@admin.register(Clinic)
class ClinicAdmin(admin.ModelAdmin):
    list_display = ['name', 'phone', 'slot_capacity', 'open_sunday', 'is_active']
    list_filter = ['is_active', 'open_sunday']
    search_fields = ['name', 'address', 'phone']


@admin.register(Doctor)
class DoctorAdmin(admin.ModelAdmin):
    list_display = ['name', 'specialty', 'clinic', 'is_active']
    list_filter = ['is_active', 'specialty', 'clinic']
    search_fields = ['name', 'specialty']
    list_select_related = ['clinic']


@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    list_display = [
        'patient_name',
        'user',
        'appointment_type',
        'doctor',
        'preferred_date',
        'preferred_time',
        'status',
        'created_at',
    ]
    list_filter = ['status', 'appointment_type', 'preferred_date', 'created_at']
    search_fields = ['patient_name', 'phone_number', 'reason_for_visit', 'user__username', 'user__email']
    list_select_related = ['user', 'doctor', 'clinic']
    date_hierarchy = 'preferred_date'
    readonly_fields = ['created_at', 'updated_at']
    actions = ['mark_confirmed', 'mark_completed', 'mark_cancelled', 'mark_missed']

    @admin.action(description='Mark selected appointments as confirmed')
    def mark_confirmed(self, request, queryset):
        # Save one-by-one so the confirmation-notification and reminder signals
        # fire per row.
        for appt in queryset.exclude(status=Appointment.Status.CONFIRMED):
            appt.status = Appointment.Status.CONFIRMED
            appt.save(update_fields=['status', 'updated_at'])

    @admin.action(description='Mark selected appointments as completed')
    def mark_completed(self, request, queryset):
        for appt in queryset.exclude(status=Appointment.Status.COMPLETED):
            appt.status = Appointment.Status.COMPLETED
            appt.save(update_fields=['status', 'updated_at'])

    @admin.action(description='Mark selected appointments as cancelled')
    def mark_cancelled(self, request, queryset):
        for appt in queryset.exclude(status=Appointment.Status.CANCELLED):
            appt.status = Appointment.Status.CANCELLED
            appt.save(update_fields=['status', 'updated_at'])

    @admin.action(description='Mark selected appointments as missed')
    def mark_missed(self, request, queryset):
        for appt in queryset.exclude(status=Appointment.Status.MISSED):
            appt.status = Appointment.Status.MISSED
            appt.save(update_fields=['status', 'updated_at'])
