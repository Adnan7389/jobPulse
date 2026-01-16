from django.contrib import admin
from django.urls import path, include
from django.http import HttpResponse

def health_check(request):
    return HttpResponse("OK")

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/health/', health_check),
    path('api/users/', include('apps.users.urls')),
    path('api/channels/', include('apps.channels.urls')),
    path('api/job_posts/', include('apps.jobs.urls')),
    path('api/notifications/', include('apps.notifications.urls')),
]
