"""
URL configuration for afya_mkononi project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
"""
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('apps.appointments.urls')),
    path('api/', include('apps.reminders.urls')),
    path('api/', include('apps.chatbot.urls')),
    path('__reload__/', include('django_browser_reload.urls')),
    path('', include('apps.frontend.urls')),
]
