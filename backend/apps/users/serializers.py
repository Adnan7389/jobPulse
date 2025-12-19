from rest_framework import serializers
from django.contrib.auth import get_user_model

User = get_user_model()

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            'username', 'telegram_id', 'skills', 'job_titles', 'preferences',
            'bio', 'experience_level', 'years_experience'
        ]
        extra_kwargs = {
            'username': {'required': False}, 
        }

    def create(self, validated_data):
        # Allow creating user by telegram_id without explicit username (generate one)
        telegram_id = validated_data.get('telegram_id')
        if not validated_data.get('username') and telegram_id:
            validated_data['username'] = f"tg_{telegram_id}"
        
        return super().create(validated_data)
