from rest_framework import generics, status
from rest_framework.response import Response
from .models import JobPost
from .serializers import JobPostSerializer

from .tasks import process_new_job_post

class JobPostCreateView(generics.CreateAPIView):
    queryset = JobPost.objects.all()
    serializer_class = JobPostSerializer

    def create(self, request, *args, **kwargs):
        # Silent duplicate handling to prevent log spam
        channel_id = request.data.get('channel_id')
        message_id = request.data.get('message_id')
        
        if JobPost.objects.filter(channel_id=channel_id, message_id=message_id).exists():
            return Response(
                {"status": "skipped", "message": "Duplicate post detected"},
                status=status.HTTP_200_OK
            )
            
        return super().create(request, *args, **kwargs)

    def perform_create(self, serializer):
        job = serializer.save()
        process_new_job_post.delay(job.id)
