from django import forms

from .models import Appointment

# Matches the brand input styling used on the booking page.
INPUT_CLASS = (
    'w-full px-3.5 py-2.5 rounded-soft border border-border focus:border-accent '
    'focus:outline-none focus:ring-2 focus:ring-accent/15 text-sm bg-background'
)


class AppointmentForm(forms.ModelForm):
    """Create / edit an appointment. Editing the date & time is how a patient
    reschedules; ``status`` is managed via dedicated actions, not this form."""

    class Meta:
        model = Appointment
        fields = (
            'patient_name', 'phone_number', 'email',
            'preferred_date', 'preferred_time', 'reason_for_visit',
        )
        widgets = {
            'preferred_date': forms.DateInput(attrs={'type': 'date'}),
            'preferred_time': forms.TimeInput(attrs={'type': 'time'}),
            'reason_for_visit': forms.Textarea(attrs={'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.setdefault('class', INPUT_CLASS)
