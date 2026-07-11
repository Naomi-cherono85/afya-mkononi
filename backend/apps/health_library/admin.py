from django.contrib import admin
from django.utils.html import format_html

from .models import Article


@admin.register(Article)
class ArticleAdmin(admin.ModelAdmin):
    list_display = ('title', 'category', 'is_published', 'updated_at')
    list_filter = ('category', 'is_published', 'updated_at')
    list_editable = ('is_published',)
    search_fields = ('title', 'summary', 'content')
    prepopulated_fields = {'slug': ('title',)}
    ordering = ('title',)
    readonly_fields = ('created_at', 'updated_at', 'image_preview')

    @admin.display(description='Preview')
    def image_preview(self, obj):
        if obj.image:
            return format_html('<img src="{}" style="max-height:120px;border-radius:8px;" />', obj.image.url)
        return 'No image uploaded.'
