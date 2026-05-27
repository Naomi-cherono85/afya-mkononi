from django.contrib import admin

from .models import ChatMessage, ChatSession


class ChatMessageInline(admin.TabularInline):
    model = ChatMessage
    extra = 0
    can_delete = False
    readonly_fields = [
        'sender_type',
        'message_content',
        'safety_category',
        'created_at',
    ]

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(ChatSession)
class ChatSessionAdmin(admin.ModelAdmin):
    list_display = ['session_id', 'user', 'started_at', 'last_active_at']
    list_filter = ['started_at', 'last_active_at']
    search_fields = ['session_id', 'user__username']
    readonly_fields = ['session_id', 'started_at', 'last_active_at']
    inlines = [ChatMessageInline]
