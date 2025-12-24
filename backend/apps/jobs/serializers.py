from rest_framework import serializers
from .models import JobPost
from apps.channels.models import Channel

class JobPostSerializer(serializers.ModelSerializer):
    channel_name = serializers.CharField(source='channel.name', read_only=True)
    channel_id = serializers.PrimaryKeyRelatedField(
        queryset=Channel.objects.all(), source='channel', write_only=True
    )

    class Meta:
        model = JobPost
        fields = [
            'id', 'channel_id', 'channel_name', 'message_id', 
            'raw_text', 'clean_text', 'source_link', 'is_processed',
            'category', 'location', 'job_type', 'work_mode'
        ]
        read_only_fields = ['is_processed', 'clean_text', 'id']
