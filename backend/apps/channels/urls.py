from django.urls import path
from .views import ChannelCreateListView, ChannelDetailView

urlpatterns = [
    path('', ChannelCreateListView.as_view(), name='channel-list-create'),
    path('<int:pk>/', ChannelDetailView.as_view(), name='channel-detail'),
]
