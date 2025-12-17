from django.urls import path
from .views import ChannelCreateListView

urlpatterns = [
    path('', ChannelCreateListView.as_view(), name='channel-list-create'),
]
