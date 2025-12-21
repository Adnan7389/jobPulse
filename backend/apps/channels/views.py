from rest_framework import generics
from .models import Channel
from .serializers import ChannelSerializer

class ChannelCreateListView(generics.ListCreateAPIView):
    queryset = Channel.objects.all()
    serializer_class = ChannelSerializer
    
    def get_queryset(self):
        """Allow filtering by added_by user"""
        queryset = Channel.objects.all()
        added_by = self.request.query_params.get('added_by')
        if added_by:
            queryset = queryset.filter(added_by=added_by)
        return queryset

class ChannelDetailView(generics.RetrieveDestroyAPIView):
    queryset = Channel.objects.all()
    serializer_class = ChannelSerializer
