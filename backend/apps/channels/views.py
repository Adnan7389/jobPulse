from rest_framework import generics
from .models import Channel
from .serializers import ChannelSerializer

class ChannelCreateListView(generics.ListCreateAPIView):
    queryset = Channel.objects.all()
    serializer_class = ChannelSerializer
