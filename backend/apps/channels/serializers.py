from rest_framework import serializers
from .models import Channel

class ChannelSerializer(serializers.ModelSerializer):
    class Meta:
        model = Channel
        fields = ['id', 'name', 'channel_username', 'channel_id', 'is_active', 'last_scraped_id']
        read_only_fields = ['last_scraped_id', 'is_active']
