from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm

from .models import Profile

User = get_user_model()

# Shared brand input styling (matches the chat input / card aesthetic).
INPUT_CLASS = (
    'w-full px-4 py-2.5 rounded-soft border border-border bg-background text-sm '
    'text-foreground placeholder:text-foreground/40 focus:border-accent '
    'focus:outline-none focus:ring-2 focus:ring-accent/20 transition'
)


def _style(fields, placeholders=None):
    """Apply the brand input class (and optional placeholders) to widgets."""
    placeholders = placeholders or {}
    for name, field in fields.items():
        css = INPUT_CLASS
        if isinstance(field.widget, forms.CheckboxInput):
            css = 'h-4 w-4 rounded border-border text-accent focus:ring-accent/30'
        field.widget.attrs.setdefault('class', css)
        if name in placeholders:
            field.widget.attrs.setdefault('placeholder', placeholders[name])


class BrandAuthenticationForm(AuthenticationForm):
    """Login form with brand-styled inputs."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        _style(self.fields, {
            'username': 'Your username',
            'password': 'Your password',
        })


class RegistrationForm(UserCreationForm):
    """Sign-up form: username + name + email + password confirmation."""

    first_name = forms.CharField(max_length=150, required=True)
    last_name = forms.CharField(max_length=150, required=False)
    email = forms.EmailField(required=True)

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ('username', 'first_name', 'last_name', 'email')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        _style(self.fields, {
            'username': 'Choose a username',
            'first_name': 'First name',
            'last_name': 'Last name',
            'email': 'you@example.com',
            'password1': 'Create a password',
            'password2': 'Confirm your password',
        })

    def save(self, commit=True):
        user = super().save(commit=False)
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data.get('last_name', '')
        user.email = self.cleaned_data['email']
        if commit:
            user.save()
        return user


class UserDetailsForm(forms.ModelForm):
    """Edit the user's name and email on the profile page."""

    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'email')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        _style(self.fields)


class ProfileForm(forms.ModelForm):
    """Edit avatar and contact details on the profile page."""

    class Meta:
        model = Profile
        fields = ('avatar', 'phone_number', 'date_of_birth')
        widgets = {
            'date_of_birth': forms.DateInput(attrs={'type': 'date'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        _style(self.fields, {'phone_number': '+254 7XX XXX XXX'})
        # File inputs get a lighter custom style instead of the boxed input.
        self.fields['avatar'].widget.attrs['class'] = (
            'block w-full text-sm text-foreground/70 file:mr-4 file:py-2 '
            'file:px-4 file:rounded-pill file:border-0 file:text-sm '
            'file:font-medium file:bg-accent-soft file:text-accent '
            'hover:file:bg-accent-tint cursor-pointer'
        )
