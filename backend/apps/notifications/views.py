from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Notification
from .serializers import NotificationSerializer

class NotificationViewSet(viewsets.ModelViewSet):
    queryset = Notification.objects.all()
    serializer_class = NotificationSerializer
    
    @action(detail=True, methods=['post'])
    def feedback(self, request, pk=None):
        """
        Submit feedback for a notification
        POST /api/notifications/{id}/feedback/
        Body: {"feedback": "relevant" | "not_relevant"}
        """
        notification = self.get_object()
        feedback_value = request.data.get('feedback')
        
        if feedback_value not in ['relevant', 'not_relevant']:
            return Response(
                {"error": "Invalid feedback value. Must be 'relevant' or 'not_relevant'."},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        notification.feedback = feedback_value
        notification.save(update_fields=['feedback'])
        
        return Response({"status": "Feedback saved", "feedback": feedback_value})
