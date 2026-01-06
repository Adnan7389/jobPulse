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
        now = timezone.now()
        today = now.date()
        last_24h = now - datetime.timedelta(hours=24)
        last_7_days = now - datetime.timedelta(days=7)
        last_30_days = now - datetime.timedelta(days=30)

        # Initialize defaults
        traffic_today = {'total': 0, 'jobs': 0}
        overall_success_rate = 100
        matches_today = 0
        matches_7d = 0
        matches_30d = 0
        matches_total = 0
        notif_stats = {}
        users_new_today = 0
        users_new_7d = 0
        users_new_30d = 0
        channels_new_today = 0
        channels_new_7d = 0
        channels_new_30d = 0
        tier_stats_list = []
        latency_stats_list = []
        ai_success_data = {'labels': ['Extraction', 'Matching'], 'success': [0, 0], 'failure': [0, 0]}

        from apps.analytics.models import AiLog, RequestMetric
        from apps.jobs.models import JobPost
        from apps.notifications.models import Notification
        from apps.users.models import User
        from apps.channels.models import Channel

        try:
            # 1. Traffic Metrics
            traffic_data = RequestMetric.objects.filter(date=today).aggregate(
                total=Sum('total_requests'),
                jobs=Sum('job_processing_requests')
            )
            if traffic_data['total']:
                traffic_today = {'total': traffic_data['total'], 'jobs': traffic_data['jobs']}

            # 2. AI Performance
            recent_logs = AiLog.objects.filter(timestamp__gte=last_24h)
            total_ai_calls = recent_logs.count()
            if total_ai_calls > 0:
                success_ai_calls = recent_logs.filter(success=True).count()
                overall_success_rate = round((success_ai_calls / total_ai_calls * 100), 1)

            tier_stats = AiLog.objects.values('tier').annotate(count=Count('id')).order_by('-count')
            tier_stats_list = list(tier_stats)

            latency_stats = recent_logs.values('tier').annotate(avg_latency=Avg('duration_ms'))
            latency_stats_list = []
            for item in latency_stats:
                latency_stats_list.append({
                    'tier': item['tier'],
                    'avg_latency': round(item['avg_latency'] or 0)
                })

            ai_success_data = {
                'labels': ['Extraction', 'Matching'],
                'success': [
                    recent_logs.filter(operation='extraction', success=True).count(),
                    recent_logs.filter(operation='matching', success=True).count()
                ],
                'failure': [
                    recent_logs.filter(operation='extraction', success=False).count(),
                    recent_logs.filter(operation='matching', success=False).count()
                ]
            }

            # 3. Business Impact (Matches)
            matches_today = Notification.objects.filter(created_at__date=today).count()
            matches_7d = Notification.objects.filter(created_at__gte=last_7_days).count()
            matches_30d = Notification.objects.filter(created_at__gte=last_30_days).count()
            matches_total = Notification.objects.count()
            
            notif_raw = Notification.objects.filter(created_at__gte=last_24h).values('status').annotate(count=Count('id'))
            notif_stats = {x['status']: x['count'] for x in notif_raw}

            # 4. Growth Metrics
            users_new_today = User.objects.filter(date_joined__date=today).count()
            users_new_7d = User.objects.filter(date_joined__gte=last_7_days).count()
            users_new_30d = User.objects.filter(date_joined__gte=last_30_days).count()
            
            channels_new_today = Channel.objects.filter(created_at__date=today).count()
            channels_new_7d = Channel.objects.filter(created_at__gte=last_7_days).count()
            channels_new_30d = Channel.objects.filter(created_at__gte=last_30_days).count()

        except Exception as e:
            # Log error but return partial dashboard
            import logging
            logging.getLogger(__name__).error(f"Dashboard Query Error: {e}")

        # 5. System Health & Logs
        from core.celery import app as celery_app
        queues = {}
        try:
            i = celery_app.control.inspect()
            queues = i.stats() or {}
        except:
            queues = {"error": "Could not connect to workers"}

        log_lines = []
        log_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'logs', 'system.log')
        if os.path.exists(log_path):
            try:
                with open(log_path, 'r') as f:
                    lines = f.readlines()
                    log_lines = [l.strip() for l in lines[-100:]]
                    log_lines.reverse()
            except:
                log_lines = ["Error reading log file"]

        latency_avg = 0
        if latency_stats_list:
            latency_avg = latency_stats_list[0].get('avg_latency', 0)

        context = {
            'title': 'System Health & Analytics (v2.2)',
            'traffic_today': traffic_today,
            'overall_success_rate': overall_success_rate,
            'matches_today': matches_today,
            'matches_7d': matches_7d,
            'matches_30d': matches_30d,
            'matches_total': matches_total,
            'queues': queues,
            'logs': log_lines,
            'users_new_today': users_new_today,
            'users_new_7d': users_new_7d,
            'users_new_30d': users_new_30d,
            'channels_new_today': channels_new_today,
            'channels_new_7d': channels_new_7d,
            'channels_new_30d': channels_new_30d,
            'ai_success_data': ai_success_data,
            'tier_labels': [x['tier'] for x in tier_stats_list],
            'tier_data': [x['count'] for x in tier_stats_list],
            'latency_avg': latency_avg,
            'notif_labels': list(notif_stats.keys()),
            'notif_data': list(notif_stats.values()),
        }
        
        return TemplateResponse(request, "admin/analytics/dashboard.html", context)
