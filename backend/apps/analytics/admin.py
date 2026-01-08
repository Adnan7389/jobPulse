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

        from apps.analytics.models import AiLog, RequestMetric
        from apps.jobs.models import JobPost
        from apps.notifications.models import Notification
        from apps.users.models import User
        from apps.channels.models import Channel

        # Prepare context with default safe values
        context = {
            'title': 'System Health & Analytics (v2.2_STABLE)',
            'traffic_today': {'total': 0, 'jobs': 0},
            'overall_success_rate': 100,
            'matches_today': 0,
            'matches_7d': 0,
            'matches_30d': 0,
            'matches_total': 0,
            'users_new_today': 0,
            'users_new_7d': 0,
            'users_new_30d': 0,
            'channels_new_today': 0,
            'channels_new_7d': 0,
            'channels_new_30d': 0,
            'ai_success_data': {'labels': ['Extraction', 'Matching'], 'success': [0, 0], 'failure': [0, 0]},
            'tier_labels': [],
            'tier_data': [],
            'latency_avg': 0,
            'notif_labels': [],
            'notif_data': [],
            'queues': {},
            'logs': [],
        }

        try:
            # 1. Traffic (Aggregated)
            traffic = RequestMetric.objects.filter(date=today).aggregate(
                total=Sum('total_requests'),
                jobs=Sum('job_processing_requests')
            )
            context['traffic_today'] = {
                'total': traffic['total'] or 0,
                'jobs': traffic['jobs'] or 0
            }

            # 2. AI Metrics (Optimized)
            recent_logs = AiLog.objects.filter(timestamp__gte=last_24h)
            ai_totals = recent_logs.aggregate(
                total_count=Count('id'),
                total_success=Count('id', filter=Q(success=True)),
                ext_success=Count('id', filter=Q(operation='extraction', success=True)),
                match_success=Count('id', filter=Q(operation='matching', success=True)),
                ext_fail=Count('id', filter=Q(operation='extraction', success=False)),
                match_fail=Count('id', filter=Q(operation='matching', success=False)),
                avg_latency_ms=Avg('duration_ms')
            )
            
            if ai_totals['total_count'] > 0:
                context['overall_success_rate'] = round((ai_totals['total_success'] / ai_totals['total_count'] * 100), 1)

            tier_stats = list(AiLog.objects.values('tier').annotate(count=Count('id')).order_by('-count'))
            context['tier_labels'] = [x['tier'] for x in tier_stats]
            context['tier_data'] = [x['count'] for x in tier_stats]
            context['latency_avg'] = round(ai_totals['avg_latency_ms'] or 0)

            context['ai_success_data']['success'] = [ai_totals['ext_success'], ai_totals['match_success']]
            context['ai_success_data']['failure'] = [ai_totals['ext_fail'], ai_totals['match_fail']]

            # 3. Growth & Business Impact
            context['matches_today'] = Notification.objects.filter(created_at__date=today).count()
            context['matches_7d'] = Notification.objects.filter(created_at__gte=last_7_days).count()
            context['matches_30d'] = Notification.objects.filter(created_at__gte=last_30_days).count()
            context['matches_total'] = Notification.objects.count()

            notif_raw = Notification.objects.filter(created_at__gte=last_24h).values('status').annotate(count=Count('id'))
            context['notif_labels'] = [x['status'] for x in notif_raw]
            context['notif_data'] = [x['count'] for x in notif_raw]

            context['users_new_today'] = User.objects.filter(date_joined__date=today).count()
            context['users_new_7d'] = User.objects.filter(date_joined__gte=last_7_days).count()
            context['users_new_30d'] = User.objects.filter(date_joined__gte=last_30_days).count()

            context['channels_new_today'] = Channel.objects.filter(created_at__date=today).count()
            context['channels_new_7d'] = Channel.objects.filter(created_at__gte=last_7_days).count()
            context['channels_new_30d'] = Channel.objects.filter(created_at__gte=last_30_days).count()

        except Exception as e:
            import logging
            logging.getLogger(__name__).error(f"Dashboard Query Error: {e}", exc_info=True)

        # 4. System Health & Logs
        from core.celery import app as celery_app
        try:
            i = celery_app.control.inspect()
            context['queues'] = i.stats() or {}
        except:
            context['queues'] = {"error": "Could not connect to workers"}

        log_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'logs', 'system.log')
        if os.path.exists(log_path):
            try:
                with open(log_path, 'r') as f:
                    lines = f.readlines()
                    log_lines = [l.strip() for l in lines[-100:]]
                    log_lines.reverse()
                    context['logs'] = log_lines
            except:
                context['logs'] = ["Error reading log file"]

        return TemplateResponse(request, "admin/analytics/dashboard.html", context)
