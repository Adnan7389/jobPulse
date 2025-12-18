from django.contrib import admin
from .models import Channel

@admin.register(Channel)
class ChannelAdmin(admin.ModelAdmin):
    list_display = ('name', 'channel_username', 'channel_id', 'last_scraped_id', 'is_active', 'created_at')
    search_fields = ('name', 'channel_username')
    list_filter = ('is_active',)
