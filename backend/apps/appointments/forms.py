from django import forms
from django.core.exceptions import ValidationError

from .models import Appointment, Clinic, Doctor
from .services.availability import validate_slot

# Matches the brand input styling used across the app.
INPUT_CLASS = (
    'w-full px-3.5 py-2.5 rounded-soft border border-border focus:border-accent '
    'focus:outline-none focus:ring-2 focus:ring-accent/15 text-sm bg-background'
)


class AppointmentForm(forms.ModelForm):
    """Create / edit / reschedule an appointment.

    Backs the server-rendered booking, edit and reschedule flows. Slot rules
    (past / closed day / fully booked) are enforced in :meth:`clean` via the
    shared :func:`validate_slot` helper.
    """

    class Meta:
        model = Appointment
        fields = (
            'patient_name', 'phone_number', 'email',
            'appointment_type', 'doctor', 'clinic',
            'preferred_date', 'preferred_time',
            'reason_for_visit', 'additional_notes',
        )
        widgets = {
            'preferred_date': forms.DateInput(attrs={'type': 'date'}),
            'preferred_time': forms.TimeInput(attrs={'type': 'time'}),
            'reason_for_visit': forms.Textarea(attrs={'rows': 3}),
            'additional_notes': forms.Textarea(attrs={'rows': 2}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Optional fields.
        self.fields['email'].required = False
        self.fields['doctor'].required = False
        self.fields['clinic'].required = False
        self.fields['additional_notes'].required = False

        # Only offer active providers, with friendly empty labels.
        self.fields['doctor'].queryset = Doctor.objects.filter(is_active=True)
        self.fields['clinic'].queryset = Clinic.objects.filter(is_active=True)
        self.fields['doctor'].empty_label = 'Any available doctor'
        self.fields['clinic'].empty_label = 'Any clinic'

        for field in self.fields.values():
            field.widget.attrs.setdefault('class', INPUT_CLASS)

    def clean(self):
        cleaned = super().clean()
        appt_date = cleaned.get('preferred_date')
        appt_time = cleaned.get('preferred_time')
        if appt_date and appt_time:
            try:
                validate_slot(
                    appt_date, appt_time,
                    clinic=cleaned.get('clinic'),
                    doctor=cleaned.get('doctor'),
                    exclude_pk=self.instance.pk,
                )
            except ValidationError as exc:
                self.add_error('preferred_time', exc)
        return cleaned
