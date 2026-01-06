from django.db import models

class AiLog(models.Model):
    TIER_CHOICES = [
        ('gemini', 'Gemini'),
        ('deepseek', 'DeepSeek'),
        ('hf', 'HuggingFace'),
        ('other', 'Other'),
    ]
    
    OPERATION_CHOICES = [
        ('extraction', 'Extraction/Classification'),
        ('matching', 'Semantic Matching'),
        ('other', 'Other'),
    ]

    tier = models.CharField(max_length=20, choices=TIER_CHOICES, db_index=True)
    operation = models.CharField(max_length=50, choices=OPERATION_CHOICES, db_index=True)
    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)
    duration_ms = models.IntegerField(help_text="Duration in milliseconds")
    success = models.BooleanField(default=True)
    tokens_used = models.IntegerField(default=0, null=True, blank=True)
    error_message = models.TextField(null=True, blank=True)
    
    # Context (optional, link to job or user if needed, but keep loose for speed)
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['tier', 'timestamp']),
            models.Index(fields=['operation', 'success']),
        ]

    def __str__(self):
        status = "OK" if self.success else "FAIL"
        return f"{self.timestamp.strftime('%H:%M:%S')} | {self.tier} | {self.operation} | {status} ({self.duration_ms}ms)"


class RequestMetric(models.Model):
    """
    Aggregates requests by hour to keep the DB light.
    We don't need to save every single HTTP request.
    """
    date = models.DateField(db_index=True)
    hour = models.IntegerField(db_index=True)  # 0-23
    
    total_requests = models.IntegerField(default=0)
    job_processing_requests = models.IntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['date', 'hour']
        ordering = ['-date', '-hour']

    def __str__(self):
        return f"{self.date} {self.hour}:00 - {self.total_requests} reqs"
