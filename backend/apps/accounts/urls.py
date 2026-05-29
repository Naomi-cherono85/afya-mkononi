from django.contrib.auth import views as auth_views
from django.urls import path, reverse_lazy

from . import views
from .forms import BrandPasswordResetForm, BrandSetPasswordForm

app_name = 'accounts'

urlpatterns = [
    path('register/', views.register, name='register'),
    path('login/', views.AfyaLoginView.as_view(), name='login'),
    path('logout/', views.AfyaLogoutView.as_view(), name='logout'),
    path('profile/', views.profile, name='profile'),

    # ----- Password reset (Django built-in views, branded templates) -----
    # Step 1: enter your email.
    path(
        'password-reset/',
        auth_views.PasswordResetView.as_view(
            template_name='accounts/password_reset.html',
            email_template_name='accounts/password_reset_email.html',
            subject_template_name='accounts/password_reset_subject.txt',
            form_class=BrandPasswordResetForm,
            success_url=reverse_lazy('accounts:password_reset_done'),
        ),
        name='password_reset',
    ),
    # Step 2: "we've emailed you a link" confirmation page.
    path(
        'password-reset/done/',
        auth_views.PasswordResetDoneView.as_view(
            template_name='accounts/password_reset_done.html',
        ),
        name='password_reset_done',
    ),
    # Step 3: the link target — verifies the token, lets the user set a new password.
    path(
        'password-reset/confirm/<uidb64>/<token>/',
        auth_views.PasswordResetConfirmView.as_view(
            template_name='accounts/password_reset_confirm.html',
            form_class=BrandSetPasswordForm,
            success_url=reverse_lazy('accounts:password_reset_complete'),
        ),
        name='password_reset_confirm',
    ),
    # Step 4: success — password changed.
    path(
        'password-reset/complete/',
        auth_views.PasswordResetCompleteView.as_view(
            template_name='accounts/password_reset_complete.html',
        ),
        name='password_reset_complete',
    ),
]
