from django.urls import path

from . import views

app_name = 'frontend'

urlpatterns = [
    path('', views.landing, name='landing'),
    path('app/', views.dashboard, name='dashboard'),
    path('appointments/book/', views.appointment_book, name='appointment-book'),
    path('reminders/new/', views.reminder_create, name='reminder-create'),
    path('chat/', views.chat, name='chat'),
    path('about/', views.about, name='about'),
]
