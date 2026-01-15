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
        is_featured = self.request.query_params.get('is_featured')
        category = self.request.query_params.get('category')
        
        if added_by:
            queryset = queryset.filter(subscribers__id=added_by)
            
        if is_featured:
             # Allow 'true', 'True', '1'
             if is_featured.lower() in ['true', '1']:
                 queryset = queryset.filter(is_featured=True)
                 
        if category:
            if category == 'general':
                queryset = queryset.filter(category='general')
            else:
                 # If user asks for 'software', give 'software' OR 'general'
                 queryset = queryset.filter(category__in=[category, 'general'])
                 
        return queryset

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # Get user ID from input (simulating 'added_by' logic passed from bot)
        # The bot sends 'added_by' in JSON, but we removed it from serializer fields.
        # We need to extract it manually or use request.user (if auth enabled).
        # Since bot uses API without Auth Token (it passes ID manually), we assume it's in request.data
        user_id = request.data.get('added_by')
        
        if user_id:
            from apps.users.models import User
            try:
                user = User.objects.get(id=user_id)
                # Check subscription limit
                if user.subscribed_channels.count() >= 5:
                    # Check if they are already subscribed to THIS channel (to allow updates/idempotency)
                    channel_username = serializer.validated_data.get('channel_username')
                    if not user.subscribed_channels.filter(channel_username=channel_username).exists():
                        return Response(
                            {"error": "You can only monitor up to 5 channels."}, 
                            status=400
                        )
            except User.DoesNotExist:
                return Response({"error": "User not found."}, status=404)

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

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        user_id = request.query_params.get('user_id')
        
        if not user_id:
            # If no user_id provided, default to standard delete (admin only?)
            # Or safeguard it. Let's safeguard.
            return Response(
                {"error": "user_id query parameter is required to unsubscribe."}, 
                status=400
            )
            
        # Unsubscribe user
        instance.subscribers.remove(user_id)
        
        # logic: if no more subscribers AND not featured, delete channel?
        # or keep it? Keeping it fills DB with junk.
        if instance.subscribers.count() == 0 and not instance.is_featured:
            self.perform_destroy(instance)
            
        return Response(status=204)
