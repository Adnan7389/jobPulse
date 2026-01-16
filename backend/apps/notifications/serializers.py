from rest_framework import serializers
from .models import Notification

class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = ['id', 'user', 'job', 'match_score', 'reasoning', 'source', 'status', 'feedback', 'created_at']
        read_only_fields = ['id', 'user', 'job', 'match_score', 'reasoning', 'source', 'status', 'created_at']
