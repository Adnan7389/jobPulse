from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/users/', include('apps.users.urls')),
    path('api/channels/', include('apps.channels.urls')),
    path('api/job_posts/', include('apps.jobs.urls')),
]
