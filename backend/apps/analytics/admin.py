from django.contrib import admin
from django.urls import path
from django.template.response import TemplateResponse
from django.db.models import Count, Avg, Sum, Q
from django.utils import timezone
from .models import AiLog, RequestMetric
import datetime
import os

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
        today = timezone.now().date()
        last_24h = timezone.now() - datetime.timedelta(hours=24)
        last_7_days = timezone.now() - datetime.timedelta(days=7)
        last_30_days = timezone.now() - datetime.timedelta(days=30)

        # 1. Traffic Metrics
        traffic_today = RequestMetric.objects.filter(date=today).aggregate(
            total=Sum('total_requests'),
            jobs=Sum('job_processing_requests')
        )
        
        # 2. AI Performance
        tier_stats = AiLog.objects.values('tier').annotate(count=Count('id')).order_by('-count')
        recent_logs = AiLog.objects.filter(timestamp__gte=last_24h)
        success_rates = recent_logs.values('operation', 'success').annotate(count=Count('id'))
        latency_stats = recent_logs.values('tier').annotate(avg_latency=Avg('duration_ms'))
        
        # Overall AI Success Rate
        total_ai_calls = recent_logs.count()
        success_ai_calls = recent_logs.filter(success=True).count()
        overall_success_rate = (success_ai_calls / total_ai_calls * 100) if total_ai_calls > 0 else 100

        # 3. Business Impact
        from apps.jobs.models import JobPost
        from apps.notifications.models import Notification
        from apps.users.models import User
        from apps.channels.models import Channel
        
        try:
            total_matches_today = Notification.objects.filter(created_at__date=today).count()
            total_matches_all = Notification.objects.count()
            # Calculate sent vs failed for last 24h
            notif_raw = Notification.objects.filter(created_at__gte=last_24h).values('status').annotate(count=Count('id'))
            notif_stats = {x['status']: x['count'] for x in notif_raw}
        except:
            total_matches_today = 0
            total_matches_all = 0
            notif_stats = {}

        # 4. System Health & Logs
        from core.celery import app as celery_app
        queues = {}
        try:
            i = celery_app.control.inspect()
            queues = i.stats() or {}
        except Exception:
            queues = {"error": "Could not connect to workers"}

        log_lines = []
        log_path = '/app/logs/system.log'
        if not os.path.exists(log_path):
             log_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'logs', 'system.log')
        
        if os.path.exists(log_path):
            with open(log_path, 'r') as f:
                lines = f.readlines()
                log_lines = lines[-100:]
                log_lines.reverse()

        # 5. Growth Metrics
        users_new_today = User.objects.filter(date_joined__date=today).count()
        users_new_7d = User.objects.filter(date_joined__gte=last_7_days).count()
        users_new_30d = User.objects.filter(date_joined__gte=last_30_days).count()
        
        channels_new_today = Channel.objects.filter(created_at__date=today).count()
        channels_new_7d = Channel.objects.filter(created_at__gte=last_7_days).count()
        channels_new_30d = Channel.objects.filter(created_at__gte=last_30_days).count()

        context = {
            'title': 'System Health & Analytics',
            'traffic_today': traffic_today,
            'overall_success_rate': round(overall_success_rate, 1),
            'matches_today': total_matches_today,
            'matches_total': total_matches_all,
            'queues': queues,
            'logs': log_lines,
            'users_new_today': users_new_today,
            'users_new_7d': users_new_7d,
            'users_new_30d': users_new_30d,
            'channels_new_today': channels_new_today,
            'channels_new_7d': channels_new_7d,
            'channels_new_30d': channels_new_30d,
            # AI Success/Fail Data for Chart
            'ai_success_data': {
                'labels': ['Extraction', 'Matching'],
                'success': [
                    recent_logs.filter(operation='extraction', success=True).count(),
                    recent_logs.filter(operation='matching', success=True).count()
                ],
                'failure': [
                    recent_logs.filter(operation='extraction', success=False).count(),
                    recent_logs.filter(operation='matching', success=False).count()
                ]
            },
            # Chart.js Data
            'tier_labels': [x['tier'] for x in tier_stats],
            'tier_data': [x['count'] for x in tier_stats],
            'latency_stats': list(latency_stats),
            'notif_labels': list(notif_stats.keys()),
            'notif_data': list(notif_stats.values()),
        }
        
        return TemplateResponse(request, "admin/analytics/dashboard.html", context)
