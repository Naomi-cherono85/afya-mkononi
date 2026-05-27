from django.contrib import admin

from .models import Appointment


@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    list_display = [
        'patient_name',
        'phone_number',
        'preferred_date',
        'preferred_time',
        'status',
        'created_at',
    ]
    list_filter = ['status', 'preferred_date']
    search_fields = ['patient_name', 'phone_number']
    readonly_fields = ['created_at', 'updated_at']
