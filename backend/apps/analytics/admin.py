from django.contrib import admin
from django.urls import path
from django.template.response import TemplateResponse
from django.db.models import Count, Avg, Sum, Q
from django.utils import timezone
from .models import AiLog, RequestMetric
import datetime
import os

# We can reuse the main admin site
class AnalyticsAdminSite(admin.AdminSite):
    site_header = "JobLens Analytics"

# Or just hook into the existing admin via a ModelAdmin or a direct view
# The prompt says "Override the default admin index or create a custom view admin/dashboard/"

# Let's register a dummy model to hang the view off of, OR just patch the admin urls.
# Patching admin urls is cleaner.

from apps.analytics.models import AiLog, RequestMetric

@admin.register(AiLog)
class AiLogAdmin(admin.ModelAdmin):
    list_display = ('timestamp', 'tier', 'operation', 'success', 'duration_ms', 'tokens_used')
    list_filter = ('tier', 'operation', 'success', 'timestamp')
    readonly_fields = ('timestamp', 'tier', 'operation', 'duration_ms', 'success', 'error_message', 'metadata')

    def get_urls(self):
        urls = super().get_urls()
        my_urls = [
            path('dashboard/', self.admin_site.admin_view(self.dashboard_view), name='analytics_dashboard'),
        ]
        return my_urls + urls

    def dashboard_view(self, request):
        # 1. Traffic Metrics
        today = timezone.now().date()
        traffic_today = RequestMetric.objects.filter(date=today).aggregate(
            total=Sum('total_requests'),
            jobs=Sum('job_processing_requests')
        )
        
        # 2. AI Performance
        # Tier Distribution
        tier_stats = AiLog.objects.values('tier').annotate(count=Count('id')).order_by('-count')
        
        # Success vs Failure (Last 24h)
        last_24h = timezone.now() - datetime.timedelta(hours=24)
        recent_logs = AiLog.objects.filter(timestamp__gte=last_24h)
        
        success_rates = recent_logs.values('operation', 'success').annotate(count=Count('id'))
        
        # Latency
        latency_stats = recent_logs.values('tier').annotate(avg_latency=Avg('duration_ms'))
        
        # 3. Business Impact (Mocked if models aren't easily accessible, but we can try to import)
        from apps.jobs.models import JobPost
        from apps.notifications.models import Notification
        
        matches_today = JobPost.objects.filter(created_at__date=today).count() # Approximation
        # Actually standard matching produces Notifications. 
        # But let's count JobPosts processed today as "Matches Found" input? 
        # Requirement: "Total Matches Found (Today / Total)"
        # This implies we should query Notifications count.
        
        try:
            total_matches_today = Notification.objects.filter(created_at__date=today).count()
            total_matches_all = Notification.objects.count()
        except:
            total_matches_today = 0
            total_matches_all = 0

        # Notifications Sent vs Failed
        # Assuming Notification model has a status field
        try:
             notif_stats = Notification.objects.values('status').annotate(count=Count('id'))
        except:
             notif_stats = []

        # 4. System Health
        # Celery Queues
        import celery
        from core.celery import app as celery_app
        
        queues = {}
        try:
            i = celery_app.control.inspect()
            # active = i.active() or {}
            # reserved = i.reserved() or {}
            # scheduled = i.scheduled() or {}
            
            # fast check for "pending" usually requires querying the broker (Redis) directly 
            # or just summing up active/reserved.
            # For MVP let's just show active tasks count if possible.
            # Note: inspect() can be slow or timeout if workers aren't responsive.
            stats = i.stats() or {}
            queues = stats
        except Exception as e:
            queues = {"error": str(e)}

        # Logs
        log_lines = []
        log_path = '/app/logs/system.log' # Docker path
        if not os.path.exists(log_path):
             # Try relative to BASE_DIR if simple python run
             log_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'logs', 'system.log')
        
        if os.path.exists(log_path):
            with open(log_path, 'r') as f:
                # Read last 100 lines efficiently-ish
                lines = f.readlines()
                log_lines = lines[-100:]
                log_lines.reverse() # Newest first

        context = {
            'title': 'System Health & Analytics',
            'traffic_today': traffic_today,
            'tier_stats': list(tier_stats),
            'success_rates': list(success_rates),
            'latency_stats': list(latency_stats),
            'matches_today': total_matches_today,
            'matches_total': total_matches_all,
            'notif_stats': list(notif_stats),
            'queues': queues,
            'logs': log_lines,
            # Pass data as JSON for charts
            'tier_labels': [x['tier'] for x in tier_stats],
            'tier_data': [x['count'] for x in tier_stats],
        }
        
        return TemplateResponse(request, "admin/analytics/dashboard.html", context)
