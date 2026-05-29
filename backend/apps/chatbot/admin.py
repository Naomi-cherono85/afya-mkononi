from django.contrib import admin

from .models import Conversation, Message


class MessageInline(admin.TabularInline):
    model = Message
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


@admin.register(Conversation)
class ConversationAdmin(admin.ModelAdmin):
    list_display = ['display_title', 'user', 'needs_human', 'created_at', 'updated_at']
    list_filter = ['needs_human', 'created_at', 'updated_at']
    search_fields = ['id', 'title', 'user__username']
    readonly_fields = ['id', 'created_at', 'updated_at']
    inlines = [MessageInline]
