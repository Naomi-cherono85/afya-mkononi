from django import forms

from .models import Reminder

# Matches the brand input styling used elsewhere.
INPUT_CLASS = (
    'w-full px-3.5 py-2.5 rounded-soft border border-border focus:border-accent '
    'focus:outline-none focus:ring-2 focus:ring-accent/15 text-sm bg-background'
)

# HTML datetime-local exchanges values in this format.
_DTL = '%Y-%m-%dT%H:%M'


class ReminderForm(forms.ModelForm):
    """Create / edit a reminder."""

    class Meta:
        model = Reminder
        fields = ('reminder_type', 'reminder_message', 'scheduled_for')
        widgets = {
            'scheduled_for': forms.DateTimeInput(attrs={'type': 'datetime-local'}, format=_DTL),
            'reminder_message': forms.Textarea(attrs={'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Accept the datetime-local wire format on input.
        self.fields['scheduled_for'].input_formats = [_DTL]
        for field in self.fields.values():
            field.widget.attrs.setdefault('class', INPUT_CLASS)
