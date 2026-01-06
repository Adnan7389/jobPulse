import time
from django.utils import timezone
from .models import RequestMetric

class MetricMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # 1. Track Request (Before processing)
        self.track_request(request)
        
        # 2. Process Request
        response = self.get_response(request)
        
        return response

    def track_request(self, request):
        # We only care about tracking general volume, and maybe specific job processing hits
        # To avoid DB write on EVERY request, we could use cache, but for MVP we use update_or_create aggregation
        
        # Skip static/media requests to avoid noise
        if request.path.startswith('/static/') or request.path.startswith('/media/'):
            return

        try:
            now = timezone.now()
            today = now.date()
            hour = now.hour
            
            # Simple aggregation: Get or Create current hour's metric
            # NOTE: For high traffic, this is a bottleneck. 
            # Better: Use Redis to incr, then Celery beat to flush to DB. 
            # Current approach: "Good enough" for MVP/Internal dashboard.
            
            # Optimization: Only update DB every N requests or use atomic update F()
            # For strict correctness we use F() objects
            from django.db.models import F
            
            is_job_process = 'process' in request.path or 'job' in request.path # Simple heuristic
            
            # We use update_or_create to ensure row exists
            metric, created = RequestMetric.objects.get_or_create(
                date=today, 
                hour=hour
            )
            
            # Atomic increment
            metric.total_requests = F('total_requests') + 1
            if is_job_process:
                metric.job_processing_requests = F('job_processing_requests') + 1
            metric.save(update_fields=['total_requests', 'job_processing_requests', 'updated_at'])
            
        except Exception as e:
            # Never crash user request due to metrics
            # logger.error(f"Metric middleware error: {e}")
            pass
