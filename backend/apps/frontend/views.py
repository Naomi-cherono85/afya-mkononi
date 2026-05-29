from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.utils import timezone

from apps.appointments.models import Appointment
from apps.reminders.models import Reminder


REMINDER_TYPE_CHOICES = Reminder.ReminderType.choices


def _greeting_for_hour(hour):
    if hour < 12:
        return 'Good morning'
    if hour < 17:
        return 'Good afternoon'
    return 'Good evening'


@login_required
def dashboard(request):
    now = timezone.localtime()
    today = now.date()

    upcoming_appointment = (
        Appointment.objects
        .filter(
            preferred_date__gte=today,
            status__in=[Appointment.Status.PENDING, Appointment.Status.CONFIRMED],
        )
        .order_by('preferred_date', 'preferred_time')
        .first()
    )

    todays_reminders = Reminder.objects.filter(
        scheduled_for__date=today,
    ).order_by('scheduled_for')[:5]

    recent_appointments = Appointment.objects.all()[:3]
    recent_reminders = Reminder.objects.all()[:3]

    context = {
        'greeting': _greeting_for_hour(now.hour),
        'today': today,
        'upcoming_appointment': upcoming_appointment,
        'todays_reminders': todays_reminders,
        'recent_appointments': recent_appointments,
        'recent_reminders': recent_reminders,
    }
    return render(request, 'frontend/pages/dashboard.html', context)


@login_required
def appointment_book(request):
    recent_appointments = Appointment.objects.all()[:5]
    return render(request, 'frontend/pages/appointment_book.html', {
        'recent_appointments': recent_appointments,
    })


@login_required
def reminder_create(request):
    recent_reminders = Reminder.objects.all()[:5]
    return render(request, 'frontend/pages/reminder_create.html', {
        'reminder_type_choices': REMINDER_TYPE_CHOICES,
        'recent_reminders': recent_reminders,
    })


@login_required
def chat(request):
    # The user's conversations power the ChatGPT-style history panel.
    conversations = request.user.conversations.all()[:50]
    return render(request, 'frontend/pages/chat.html', {
        'conversations': conversations,
    })


def about(request):
    return render(request, 'frontend/pages/about.html')
