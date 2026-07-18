from django.urls import path

from . import views

app_name = 'frontend'

urlpatterns = [
    path('', views.landing, name='landing'),
    path('app/', views.dashboard, name='dashboard'),
    path('appointments/', views.appointment_list, name='appointment-list'),
    path('appointments/book/', views.appointment_book, name='appointment-book'),
    path('appointments/<int:pk>/', views.appointment_detail, name='appointment-detail'),
    path('appointments/<int:pk>/success/', views.appointment_success, name='appointment-success'),
    path('appointments/<int:pk>/edit/', views.appointment_edit, name='appointment-edit'),
    path('appointments/<int:pk>/reschedule/', views.appointment_reschedule, name='appointment-reschedule'),
    path('appointments/<int:pk>/cancel/', views.appointment_cancel, name='appointment-cancel'),
    path('reminders/', views.reminder_list, name='reminder-list'),
    path('reminders/new/', views.reminder_create, name='reminder-create'),
    path('reminders/<int:pk>/edit/', views.reminder_edit, name='reminder-edit'),
    path('reminders/<int:pk>/complete/', views.reminder_complete, name='reminder-complete'),
    path('reminders/<int:pk>/snooze/', views.reminder_snooze, name='reminder-snooze'),
    path('reminders/<int:pk>/delete/', views.reminder_delete, name='reminder-delete'),
    path('library/', views.library_list, name='library'),
    path('library/<slug:slug>/', views.library_article, name='library-article'),
    path('search/', views.search, name='search'),
    path('search/results/', views.search_results, name='search-results'),
    path('notifications/', views.notification_list, name='notifications'),
    path('notifications/<int:pk>/read/', views.notification_mark_read, name='notification-read'),
    path('notifications/read-all/', views.notification_mark_all_read, name='notification-read-all'),
    path('chat/', views.chat, name='chat'),
    path('about/', views.about, name='about'),
]
