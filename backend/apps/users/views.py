from rest_framework import generics
from .serializers import UserSerializer
from django.contrib.auth import get_user_model
from rest_framework.response import Response

User = get_user_model()

class UserListCreateView(generics.ListCreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    
    def get_queryset(self):
        """Allow filtering by telegram_id"""
        queryset = User.objects.all()
        telegram_id = self.request.query_params.get('telegram_id')
        if telegram_id:
            queryset = queryset.filter(telegram_id=telegram_id)
        return queryset

    def create(self, request, *args, **kwargs):
        """
        Custom create that performs an update if the telegram_id already exists.
        This provides an 'upsert' behavior for the bot onboarding.
        """
        telegram_id = request.data.get('telegram_id')
        if telegram_id:
            user = User.objects.filter(telegram_id=telegram_id).first()
            if user:
                serializer = self.get_serializer(user, data=request.data, partial=True)
                serializer.is_valid(raise_exception=True)
                serializer.save()
                return Response(serializer.data)
        
        return super().create(request, *args, **kwargs)

class UserDetailView(generics.RetrieveUpdateAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer
