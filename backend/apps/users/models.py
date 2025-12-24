from django.contrib.auth.models import AbstractUser
from django.db import models
from django.contrib.postgres.fields import ArrayField

class User(AbstractUser):
    telegram_id = models.BigIntegerField(unique=True, null=True, blank=True)
    skills = ArrayField(models.CharField(max_length=100), blank=True, default=list)
    job_titles = ArrayField(
        models.CharField(max_length=100), 
        blank=True, 
        default=list,
        help_text="Desired job roles (e.g., 'Backend Developer', 'DevOps Engineer')"
    )
    preferences = models.JSONField(default=dict, blank=True)
    
    # AI Matching Enhancement Fields
    bio = models.TextField(
        blank=True, 
        help_text="User's self-description for AI-powered job matching"
    )
    experience_level = models.CharField(
        max_length=20,
        choices=[
            ('junior', 'Junior (0-2 years)'),
            ('mid', 'Mid-level (2-5 years)'),
            ('senior', 'Senior (5+ years)'),
            ('lead', 'Lead/Principal (8+ years)')
        ],
        blank=True,
        help_text="Experience level for job matching"
    )
    years_experience = models.PositiveIntegerField(
        null=True, 
        blank=True,
        help_text="Total years of professional experience"
    )
    
    # Structured Filtering Preferences
    preferred_category = models.CharField(
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
    preferred_location = models.CharField(max_length=100, blank=True, null=True)
    preferred_mode = models.CharField(
        max_length=20,
        choices=[
            ('remote', 'Remote'),
            ('hybrid', 'Hybrid'),
            ('onsite', 'On-site'),
            ('all', 'Any / All')
        ],
        default='all'
    )
    preferred_type = models.CharField(
        max_length=20,
        choices=[
            ('full_time', 'Full-time'),
            ('part_time', 'Part-time'),
            ('all', 'Any / All')
        ],
        default='all'
    )
    
    def __str__(self):
        return f"{self.username} ({self.telegram_id})"
