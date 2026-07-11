from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView, LogoutView
from django.shortcuts import redirect, render
from django.urls import reverse_lazy

from .forms import (
    AvatarForm,
    BrandAuthenticationForm,
    ProfileForm,
    RegistrationForm,
    UserDetailsForm,
)
from .models import BUILTIN_AVATARS, BUILTIN_AVATAR_KEYS


def register(request):
    """Create a new account, log the user in, and send them to the dashboard."""
    if request.user.is_authenticated:
        return redirect('frontend:dashboard')

    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, 'Welcome to Afya Mkononi! Your account is ready.')
            return redirect('frontend:dashboard')
    else:
        form = RegistrationForm()

    return render(request, 'accounts/register.html', {'form': form})


class AfyaLoginView(LoginView):
    template_name = 'accounts/login.html'
    authentication_form = BrandAuthenticationForm
    redirect_authenticated_user = True


class AfyaLogoutView(LogoutView):
    next_page = reverse_lazy('accounts:login')


@login_required
def profile(request):
    """View and edit the signed-in user's account details and profile picture.

    A single page handles several distinct actions, dispatched by a hidden
    ``action`` field so each control (details form, photo upload, built-in
    avatar picker, remove photo) can be submitted on its own.
    """
    user = request.user
    profile = user.profile
    user_form = UserDetailsForm(instance=user)
    profile_form = ProfileForm(instance=profile)

    if request.method == 'POST':
        action = request.POST.get('action', 'save_details')

        if action == 'upload_avatar':
            avatar_form = AvatarForm(request.POST, request.FILES, instance=profile)
            if avatar_form.is_valid() and avatar_form.cleaned_data.get('avatar'):
                obj = avatar_form.save(commit=False)
                obj.avatar_choice = ''  # an uploaded photo supersedes a built-in
                obj.save()
                _notify_profile_updated(user)
                messages.success(request, 'Your profile picture has been updated.')
                return redirect('accounts:profile')
            messages.error(request, 'Please choose a valid image to upload.')

        elif action == 'choose_avatar':
            choice = request.POST.get('avatar_choice', '')
            if choice in BUILTIN_AVATAR_KEYS:
                if profile.avatar:
                    profile.avatar.delete(save=False)
                profile.avatar = ''
                profile.avatar_choice = choice
                profile.save()
                _notify_profile_updated(user)
                messages.success(request, 'Your profile picture has been updated.')
            return redirect('accounts:profile')

        elif action == 'delete_avatar':
            if profile.avatar:
                profile.avatar.delete(save=False)
            profile.avatar = ''
            profile.avatar_choice = ''
            profile.save()
            messages.success(request, 'Your profile picture has been removed.')
            return redirect('accounts:profile')

        else:  # save_details
            user_form = UserDetailsForm(request.POST, instance=user)
            profile_form = ProfileForm(request.POST, instance=profile)
            if user_form.is_valid() and profile_form.is_valid():
                user_form.save()
                profile_form.save()
                _notify_profile_updated(user)
                messages.success(request, 'Your profile has been updated.')
                return redirect('accounts:profile')

    return render(request, 'accounts/profile.html', {
        'user_form': user_form,
        'profile_form': profile_form,
        'avatar_form': AvatarForm(instance=profile),
        'builtin_avatars': BUILTIN_AVATARS,
    })


def _notify_profile_updated(user):
    """Record a 'profile updated' notification.

    Imported lazily so the accounts app doesn't hard-depend on the
    notifications app (kept optional / decoupled).
    """
    try:
        from apps.notifications.models import Notification
    except Exception:
        return
    Notification.notify(
        user,
        kind=Notification.Kind.PROFILE_UPDATED,
        title='Profile updated',
        message='Your profile details were updated.',
    )
