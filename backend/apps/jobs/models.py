from django.db import models
from apps.channels.models import Channel

class JobPost(models.Model):
    channel = models.ForeignKey(Channel, on_delete=models.CASCADE, related_name='posts')
    message_id = models.BigIntegerField(help_text="Telegram Message ID in the channel")
    raw_text = models.TextField(help_text="Original raw text from Telegram")
    clean_text = models.TextField(blank=True, help_text="Text cleaned for matching")
    source_link = models.URLField(max_length=500, help_text="Direct link to the post")
    published_at = models.DateTimeField(null=True, blank=True)
    is_processed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('channel', 'message_id')
        indexes = [
            models.Index(fields=['is_processed', 'created_at']),
        ]

    def __str__(self):
        return f"{self.channel.name} [{self.message_id}]"
