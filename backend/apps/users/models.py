from django.contrib.auth.models import AbstractUser
from django.db import models
from django.contrib.postgres.fields import ArrayField

class User(AbstractUser):
    telegram_id = models.BigIntegerField(unique=True, null=True, blank=True)
    skills = ArrayField(models.CharField(max_length=100), blank=True, default=list)
    preferences = models.JSONField(default=dict, blank=True)
    
    def __str__(self):
        return f"{self.username} ({self.telegram_id})"
