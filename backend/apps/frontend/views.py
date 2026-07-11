from datetime import timedelta

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_POST

from apps.appointments.forms import AppointmentForm
from apps.appointments.models import Appointment
from apps.core.greetings import pick_greeting
from apps.health_library.models import Article
from apps.notifications.models import Notification
from apps.reminders.forms import ReminderForm
from apps.reminders.models import Reminder


REMINDER_TYPE_CHOICES = Reminder.ReminderType.choices


def landing(request):
    # Public marketing page. Signed-in users skip straight to their dashboard.
    if request.user.is_authenticated:
        return redirect('frontend:dashboard')
    return render(request, 'frontend/pages/landing.html')


@login_required
def dashboard(request):
    now = timezone.localtime()
    today = now.date()

    # Set at login by the user_logged_in signal; fall back for older sessions.
    greeting = request.session.get('greeting')
    if not greeting:
        greeting = pick_greeting()
        request.session['greeting'] = greeting

    upcoming_appointment = (
        Appointment.objects
        .filter(
            user=request.user,
            preferred_date__gte=today,
            status__in=[Appointment.Status.PENDING, Appointment.Status.CONFIRMED],
        )
        .order_by('preferred_date', 'preferred_time')
        .first()
    )

    todays_reminders = Reminder.objects.filter(
        user=request.user,
        scheduled_for__date=today,
    ).order_by('scheduled_for')[:5]

    recent_appointments = Appointment.objects.filter(user=request.user)[:3]
    recent_reminders = Reminder.objects.filter(user=request.user)[:3]

    next_reminder = (
        Reminder.objects
        .filter(user=request.user, status=Reminder.Status.PENDING, scheduled_for__gte=now)
        .order_by('scheduled_for')
        .first()
    )
    recent_conversation = request.user.conversations.first()

    quick_stats = {
        'upcoming_appointments': Appointment.objects.filter(
            user=request.user, preferred_date__gte=today,
            status__in=[Appointment.Status.PENDING, Appointment.Status.CONFIRMED],
        ).count(),
        'pending_reminders': Reminder.objects.filter(
            user=request.user, status=Reminder.Status.PENDING,
        ).count(),
        'conversations': request.user.conversations.count(),
        'unread_notifications': request.user.notifications.filter(is_read=False).count(),
    }

    context = {
        'greeting': greeting,
        'today': today,
        'upcoming_appointment': upcoming_appointment,
        'todays_reminders': todays_reminders,
        'recent_appointments': recent_appointments,
        'recent_reminders': recent_reminders,
        'next_reminder': next_reminder,
        'recent_conversation': recent_conversation,
        'quick_stats': quick_stats,
    }
    return render(request, 'frontend/pages/dashboard.html', context)


@login_required
def appointment_book(request):
    recent_appointments = Appointment.objects.filter(user=request.user)[:5]
    return render(request, 'frontend/pages/appointment_book.html', {
        'recent_appointments': recent_appointments,
    })


@login_required
def reminder_create(request):
    recent_reminders = Reminder.objects.filter(user=request.user)[:5]
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


@login_required
def appointment_list(request):
    """All of the signed-in user's appointments, searchable and paginated."""
    q = request.GET.get('q', '').strip()
    appointments = Appointment.objects.filter(user=request.user)
    if q:
        appointments = appointments.filter(
            Q(patient_name__icontains=q)
            | Q(reason_for_visit__icontains=q)
            | Q(phone_number__icontains=q)
        )
    page = Paginator(appointments, 10).get_page(request.GET.get('page'))
    return render(request, 'frontend/pages/appointment_list.html', {
        'appointments': page,
        'q': q,
    })


@login_required
def appointment_detail(request, pk):
    appointment = get_object_or_404(Appointment, pk=pk, user=request.user)
    return render(request, 'frontend/pages/appointment_detail.html', {
        'appointment': appointment,
    })


@login_required
def appointment_edit(request, pk):
    """Edit an appointment — this is also how a patient reschedules (date/time)."""
    appointment = get_object_or_404(Appointment, pk=pk, user=request.user)
    if request.method == 'POST':
        form = AppointmentForm(request.POST, instance=appointment)
        if form.is_valid():
            form.save()
            messages.success(request, 'Your appointment has been updated.')
            return redirect('frontend:appointment-detail', pk=appointment.pk)
    else:
        form = AppointmentForm(instance=appointment)
    return render(request, 'frontend/pages/appointment_edit.html', {
        'form': form,
        'appointment': appointment,
    })


@login_required
@require_POST
def appointment_cancel(request, pk):
    appointment = get_object_or_404(Appointment, pk=pk, user=request.user)
    appointment.status = Appointment.Status.CANCELLED
    appointment.save(update_fields=['status', 'updated_at'])
    messages.success(request, 'Your appointment has been cancelled.')
    return redirect('frontend:appointment-detail', pk=appointment.pk)


@login_required
def reminder_list(request):
    """The user's reminders, split into Upcoming (pending) and Completed tabs."""
    tab = request.GET.get('tab', 'upcoming')
    q = request.GET.get('q', '').strip()
    base = Reminder.objects.filter(user=request.user)

    if tab == 'completed':
        reminders = base.filter(status=Reminder.Status.COMPLETED).order_by('-scheduled_for')
    else:
        tab = 'upcoming'
        reminders = base.filter(status=Reminder.Status.PENDING).order_by('scheduled_for')

    if q:
        reminders = reminders.filter(
            Q(reminder_message__icontains=q) | Q(patient_name__icontains=q)
        )

    page = Paginator(reminders, 10).get_page(request.GET.get('page'))
    return render(request, 'frontend/pages/reminder_list.html', {
        'reminders': page,
        'tab': tab,
        'q': q,
        'upcoming_count': base.filter(status=Reminder.Status.PENDING).count(),
        'completed_count': base.filter(status=Reminder.Status.COMPLETED).count(),
    })


@login_required
def reminder_edit(request, pk):
    reminder = get_object_or_404(Reminder, pk=pk, user=request.user)
    if request.method == 'POST':
        form = ReminderForm(request.POST, instance=reminder)
        if form.is_valid():
            form.save()
            messages.success(request, 'Your reminder has been updated.')
            return redirect('frontend:reminder-list')
    else:
        form = ReminderForm(instance=reminder)
    return render(request, 'frontend/pages/reminder_edit.html', {
        'form': form,
        'reminder': reminder,
    })


@login_required
@require_POST
def reminder_complete(request, pk):
    reminder = get_object_or_404(Reminder, pk=pk, user=request.user)
    reminder.status = Reminder.Status.COMPLETED
    reminder.completed_at = timezone.now()
    reminder.save(update_fields=['status', 'completed_at'])
    Notification.notify(
        request.user,
        kind=Notification.Kind.REMINDER_COMPLETED,
        title='Reminder completed',
        message=reminder.reminder_message[:120],
        url=reverse('frontend:reminder-list'),
    )
    messages.success(request, 'Reminder marked as completed.')
    return redirect('frontend:reminder-list')


@login_required
@require_POST
def reminder_snooze(request, pk):
    """Push a reminder one day forward (keeps it pending)."""
    reminder = get_object_or_404(Reminder, pk=pk, user=request.user)
    reminder.scheduled_for = reminder.scheduled_for + timedelta(days=1)
    reminder.status = Reminder.Status.PENDING
    reminder.save(update_fields=['scheduled_for', 'status'])
    messages.success(request, 'Reminder snoozed to tomorrow.')
    return redirect('frontend:reminder-list')


@login_required
@require_POST
def reminder_delete(request, pk):
    reminder = get_object_or_404(Reminder, pk=pk, user=request.user)
    reminder.delete()
    messages.success(request, 'Reminder deleted.')
    return redirect('frontend:reminder-list')


@login_required
def notification_list(request):
    notifications = Notification.objects.filter(user=request.user)
    page = Paginator(notifications, 15).get_page(request.GET.get('page'))
    return render(request, 'frontend/pages/notifications.html', {
        'notifications': page,
    })


@login_required
@require_POST
def notification_mark_read(request, pk):
    notification = get_object_or_404(Notification, pk=pk, user=request.user)
    if not notification.is_read:
        notification.is_read = True
        notification.save(update_fields=['is_read'])
    # Follow the notification's link if it has one, otherwise back to the list.
    return redirect(notification.url or 'frontend:notifications')


@login_required
@require_POST
def notification_mark_all_read(request):
    Notification.objects.filter(user=request.user, is_read=False).update(is_read=True)
    messages.success(request, 'All notifications marked as read.')
    return redirect('frontend:notifications')


@login_required
def search(request):
    """Search landing page. Results are fetched live from ``search_results``."""
    return render(request, 'frontend/pages/search.html', {
        'q': request.GET.get('q', '').strip(),
    })


@login_required
def search_results(request):
    """JSON search across the signed-in user's own conversations, appointments
    and reminders. Powers the instant/live search box."""
    q = request.GET.get('q', '').strip()
    data = {'appointments': [], 'reminders': [], 'conversations': [], 'query': q}
    if q:
        appts = (
            Appointment.objects.filter(user=request.user)
            .filter(Q(patient_name__icontains=q) | Q(reason_for_visit__icontains=q))[:8]
        )
        data['appointments'] = [{
            'title': a.reason_for_visit[:70] or 'Appointment',
            'subtitle': f'{a.preferred_date:%d %b %Y} · {a.get_status_display()}',
            'url': reverse('frontend:appointment-detail', args=[a.pk]),
        } for a in appts]

        reminders = (
            Reminder.objects.filter(user=request.user)
            .filter(Q(reminder_message__icontains=q))[:8]
        )
        data['reminders'] = [{
            'title': r.reminder_message[:70],
            'subtitle': f'{r.scheduled_for:%d %b %Y} · {r.get_status_display()}',
            'url': reverse('frontend:reminder-list'),
        } for r in reminders]

        convs = (
            request.user.conversations
            .filter(Q(title__icontains=q) | Q(messages__message_content__icontains=q))
            .distinct()[:8]
        )
        data['conversations'] = [{
            'title': c.display_title,
            'subtitle': 'Conversation',
            'url': reverse('frontend:chat'),
        } for c in convs]

    return JsonResponse(data)


@login_required
def library_list(request):
    """The Health Library — searchable, filterable by category, paginated."""
    q = request.GET.get('q', '').strip()
    category = request.GET.get('category', '').strip()
    articles = Article.objects.filter(is_published=True)
    if category:
        articles = articles.filter(category=category)
    if q:
        articles = articles.filter(
            Q(title__icontains=q) | Q(summary__icontains=q) | Q(content__icontains=q)
        )
    page = Paginator(articles, 9).get_page(request.GET.get('page'))
    return render(request, 'frontend/pages/library_list.html', {
        'articles': page,
        'q': q,
        'category': category,
        'categories': Article.Category.choices,
    })


@login_required
def library_article(request, slug):
    article = get_object_or_404(Article, slug=slug, is_published=True)
    related = (
        Article.objects.filter(is_published=True, category=article.category)
        .exclude(pk=article.pk)[:3]
    )
    return render(request, 'frontend/pages/article_detail.html', {
        'article': article,
        'related': related,
    })


def about(request):
    return render(request, 'frontend/pages/about.html')
