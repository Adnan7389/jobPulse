from rest_framework import generics
from .models import JobPost
from .serializers import JobPostSerializer

from .tasks import process_new_job_post

class JobPostCreateView(generics.CreateAPIView):
    queryset = JobPost.objects.all()
    serializer_class = JobPostSerializer

    def perform_create(self, serializer):
        job = serializer.save()
        process_new_job_post.delay(job.id)
