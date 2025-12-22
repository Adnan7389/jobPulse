from rest_framework import generics
from rest_framework.response import Response
from .models import Channel
from .serializers import ChannelSerializer

class ChannelCreateListView(generics.ListCreateAPIView):
    queryset = Channel.objects.all()
    serializer_class = ChannelSerializer
    
    def get_queryset(self):
        """Allow filtering by added_by user (now subscribers)"""
        queryset = Channel.objects.all()
        added_by = self.request.query_params.get('added_by')
        if added_by:
            queryset = queryset.filter(subscribers__id=added_by)
        return queryset

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # Get user ID from input (simulating 'added_by' logic passed from bot)
        # The bot sends 'added_by' in JSON, but we removed it from serializer fields.
        # We need to extract it manually or use request.user (if auth enabled).
        # Since bot uses API without Auth Token (it passes ID manually), we assume it's in request.data
        user_id = request.data.get('added_by')
        
        channel_username = serializer.validated_data.get('channel_username')
        name = serializer.validated_data.get('name')
        
        # Get or Create Channel
        channel, created = Channel.objects.get_or_create(
            channel_username=channel_username,
            defaults={'name': name}
        )
        
        if user_id:
            channel.subscribers.add(user_id)
            
        headers = self.get_success_headers(serializer.data)
        # Return 201 Created or 200 OK
        status_code = 201 if created else 200
        
        # Return serialized data of the instance
        return_serializer = self.get_serializer(channel)
        return Response(return_serializer.data, status=status_code, headers=headers)

class ChannelDetailView(generics.RetrieveDestroyAPIView):
    queryset = Channel.objects.all()
    serializer_class = ChannelSerializer
