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

class UserDetailView(generics.RetrieveUpdateAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer
