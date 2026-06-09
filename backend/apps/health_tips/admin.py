from django.contrib import admin
from django.utils.html import format_html

from .models import HealthTip


@admin.register(HealthTip)
class HealthTipAdmin(admin.ModelAdmin):
    list_display = ('title', 'category', 'is_active', 'created_at')
    list_filter = ('category', 'is_active', 'created_at')
    list_editable = ('is_active',)
    search_fields = ('title', 'content')
    ordering = ('-created_at',)
    readonly_fields = ('created_at', 'updated_at', 'image_preview')
    fields = (
        'title',
        'content',
        'category',
        'image',
        'image_preview',
        'is_active',
        'created_at',
        'updated_at',
    )

    @admin.display(description='Preview')
    def image_preview(self, obj):
        if obj.image:
            return format_html(
                '<img src="{}" style="max-height:120px;border-radius:8px;" />',
                obj.image.url,
            )
        return 'No image uploaded.'
