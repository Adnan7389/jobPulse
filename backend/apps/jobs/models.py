from django.db import models
from apps.channels.models import Channel

class JobPost(models.Model):
    channel = models.ForeignKey(Channel, on_delete=models.CASCADE, related_name='posts')
    message_id = models.BigIntegerField(help_text="Telegram Message ID in the channel")
    raw_text = models.TextField(help_text="Original raw text from Telegram")
    clean_text = models.TextField(blank=True, help_text="Text cleaned for matching")
    source_link = models.URLField(max_length=500, help_text="Direct link to the post")
    published_at = models.DateTimeField(null=True, blank=True)
    
    # Extracted Metadata
    category = models.CharField(
        max_length=50,
        choices=[
            ('software', 'Software Development'),
            ('marketing', 'Marketing'),
            ('design', 'Design'),
            ('sales', 'Sales'),
            ('finance', 'Finance'),
            ('hr', 'Human Resources'),
            ('customer_service', 'Customer Service'),
            ('management', 'Management'),
            ('other', 'Other'),
        ],
        blank=True,
        null=True
    )
    location = models.CharField(max_length=100, blank=True, null=True)
    job_type = models.CharField(
        max_length=20,
        choices=[
            ('full_time', 'Full-time'),
            ('part_time', 'Part-time'),
        ],
        blank=True,
        null=True
    )
    work_mode = models.CharField(
        max_length=20,
        choices=[
            ('remote', 'Remote'),
            ('hybrid', 'Hybrid'),
            ('onsite', 'On-site'),
        ],
        blank=True,
        null=True
    )
    
    is_processed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('channel', 'message_id')
        indexes = [
            models.Index(fields=['is_processed', 'created_at']),
        ]

    def __str__(self):
        return f"{self.channel.name} [{self.message_id}]"
