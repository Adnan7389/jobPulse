from django.contrib import admin
from .models import JobPost

@admin.register(JobPost)
class JobPostAdmin(admin.ModelAdmin):
    list_display = ('channel', 'message_id', 'category', 'work_mode', 'is_processed', 'created_at')
    list_filter = ('is_processed', 'category', 'work_mode', 'job_type', 'channel')
    search_fields = ('raw_text', 'location')
