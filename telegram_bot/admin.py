from django.contrib import admin
from django.utils.html import format_html
from .models import TelegramUser


@admin.register(TelegramUser)
class TelegramUserAdmin(admin.ModelAdmin):
    """Admin interface for Telegram users."""
    
    list_display = [
        'telegram_id', 'username', 'full_name', 
        'created_at', 'last_seen'
    ]
    list_filter = [
        'created_at', 'last_seen'
    ]
    search_fields = ['telegram_id', 'username', 'first_name', 'last_name']
    readonly_fields = ['telegram_id', 'created_at', 'updated_at']
    ordering = ['-created_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('telegram_id', 'first_name', 'last_name', 'username')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at', 'last_seen'),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        """Optimize queryset for admin list view."""
        return super().get_queryset(request).select_related()
