from django.db import models
from django.conf import settings

class Channel(models.Model):
    name = models.CharField(max_length=255, help_text="Human readable name (e.g. Python Jobs)")
    channel_username = models.CharField(max_length=255, unique=True, help_text="Telegram username WITHOUT @ (e.g. pythonjobs)")
    channel_id = models.BigIntegerField(unique=True, null=True, blank=True, help_text="Telegram Channel ID (Auto-populated if possible)")
    last_scraped_id = models.IntegerField(default=0, help_text="ID of the last message scraped")
    is_active = models.BooleanField(default=True)
    subscribers = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name='subscribed_channels', blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name or self.channel_username
