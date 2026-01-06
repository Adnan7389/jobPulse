from django.contrib import admin
from .models import Notification

@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'job', 'match_score', 'status', 'is_sent', 'created_at')
    list_filter = ('status', 'is_sent', 'created_at', 'source')
    search_fields = ('user__username', 'job__raw_text', 'reasoning')
    readonly_fields = ('created_at',)
