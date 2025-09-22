from django.db import models
from django.utils import timezone


class TelegramUser(models.Model):
    """Model to store Telegram user information."""
    
    # Telegram user ID (unique identifier from Telegram)
    telegram_id = models.BigIntegerField(unique=True, db_index=True)
    
    # User's display name (first_name + last_name from Telegram)
    first_name = models.CharField(max_length=255, blank=True, null=True)
    last_name = models.CharField(max_length=255, blank=True, null=True)
    
    # Username (without @)
    username = models.CharField(max_length=255, blank=True, null=True, db_index=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_seen = models.DateTimeField(default=timezone.now)
    
    class Meta:
        db_table = 'telegram_users'
        verbose_name = 'Telegram User'
        verbose_name_plural = 'Telegram Users'
        ordering = ['-created_at']
    
    def __str__(self):
        if self.username:
            return f"@{self.username} ({self.telegram_id})"
        elif self.first_name:
            return f"{self.first_name} {self.last_name or ''}".strip() + f" ({self.telegram_id})"
        else:
            return f"User {self.telegram_id}"
    
    @property
    def full_name(self):
        """Return the full name of the user."""
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        elif self.first_name:
            return self.first_name
        elif self.last_name:
            return self.last_name
        else:
            return "Unknown"
    
    def update_last_seen(self):
        """Update the last_seen timestamp to now."""
        self.last_seen = timezone.now()
        self.save(update_fields=['last_seen'])
