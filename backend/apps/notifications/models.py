from django.db import models
from django.conf import settings
from apps.jobs.models import JobPost

class Notification(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='notifications')
    job = models.ForeignKey(JobPost, on_delete=models.CASCADE, related_name='notifications')
    match_score = models.PositiveIntegerField(null=True, blank=True)
    reasoning = models.TextField(blank=True)
    source = models.CharField(max_length=50, default='keyword', help_text="Source of the match (e.g., gemini, keyword)")
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('sent', 'Sent'),
        ('failed', 'Failed'),
    ]
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    is_sent = models.BooleanField(default=False)
    FEEDBACK_CHOICES = [
        ('pending', 'Pending'),
        ('relevant', 'Relevant'),
        ('not_relevant', 'Not Relevant'),
    ]
    feedback = models.CharField(max_length=15, choices=FEEDBACK_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'job')
        ordering = ['-created_at']

    def __str__(self):
        return f"Notification: {self.user} - {self.job}"
