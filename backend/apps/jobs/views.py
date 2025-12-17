from rest_framework import generics
from .models import JobPost
from .serializers import JobPostSerializer

class JobPostCreateView(generics.CreateAPIView):
    queryset = JobPost.objects.all()
    serializer_class = JobPostSerializer
