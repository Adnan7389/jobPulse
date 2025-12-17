from django.urls import path
from .views import JobPostCreateView

urlpatterns = [
    path('', JobPostCreateView.as_view(), name='job-create'),
]
