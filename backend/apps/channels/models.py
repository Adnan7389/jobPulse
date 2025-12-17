from django.db import models
from django.conf import settings

class Channel(models.Model):
    name = models.CharField(max_length=255, unique=True, help_text="Channel username (e.g. @jobs)")
    channel_id = models.BigIntegerField(unique=True, null=True, blank=True, help_text="Telegram Channel ID")
    last_scraped_id = models.IntegerField(default=0, help_text="ID of the last message scraped")
    is_active = models.BooleanField(default=True)
    added_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='added_channels')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name
