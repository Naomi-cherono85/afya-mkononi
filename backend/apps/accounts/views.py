from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView, LogoutView
from django.shortcuts import redirect, render
from django.urls import reverse_lazy

from .forms import (
    BrandAuthenticationForm,
    ProfileForm,
    RegistrationForm,
    UserDetailsForm,
)


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
    """View and edit the signed-in user's account details and avatar."""
    user = request.user
    if request.method == 'POST':
        user_form = UserDetailsForm(request.POST, instance=user)
        profile_form = ProfileForm(request.POST, request.FILES, instance=user.profile)
        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
            messages.success(request, 'Your profile has been updated.')
            return redirect('accounts:profile')
    else:
        user_form = UserDetailsForm(instance=user)
        profile_form = ProfileForm(instance=user.profile)

    return render(request, 'accounts/profile.html', {
        'user_form': user_form,
        'profile_form': profile_form,
    })
