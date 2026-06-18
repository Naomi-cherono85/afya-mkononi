from django.contrib import admin

from .models import ChatAttachment, Conversation, Message


class ChatAttachmentInline(admin.TabularInline):
    model = ChatAttachment
    extra = 0
    can_delete = False
    readonly_fields = ['file', 'original_name', 'kind', 'content_type', 'created_at']

    def has_add_permission(self, request, obj=None):
        return False


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


@admin.register(ChatAttachment)
class ChatAttachmentAdmin(admin.ModelAdmin):
    list_display = ['name', 'kind', 'message', 'created_at']
    list_filter = ['kind', 'created_at']
    search_fields = ['original_name', 'message__conversation__id']
    readonly_fields = ['created_at']


@admin.register(Conversation)
class ConversationAdmin(admin.ModelAdmin):
    list_display = ['display_title', 'user', 'needs_human', 'created_at', 'updated_at']
    list_filter = ['needs_human', 'created_at', 'updated_at']
    search_fields = ['id', 'title', 'user__username']
    readonly_fields = ['id', 'created_at', 'updated_at']
    inlines = [MessageInline]
