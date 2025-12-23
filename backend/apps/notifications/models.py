from django.db import models
from django.conf import settings
from apps.jobs.models import JobPost

class Notification(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='notifications')
    job = models.ForeignKey(JobPost, on_delete=models.CASCADE, related_name='notifications')
    is_sent = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'job')
        ordering = ['-created_at']

    def __str__(self):
        return f"Notification: {self.user} - {self.job}"
