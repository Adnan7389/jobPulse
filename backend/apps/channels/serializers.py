from rest_framework import serializers
from .models import Channel

class ChannelSerializer(serializers.ModelSerializer):
    class Meta:
        model = Channel
        fields = ['name', 'channel_id', 'is_active', 'last_scraped_id']
        read_only_fields = ['last_scraped_id', 'is_active']
