from django.urls import re_path
from . import consumers


websocket_urlpatterns = [
    re_path(r'ws/network/$', consumers.NetworkConsumer.as_asgi()),
    # re_path(r'ws/anomaly-logs/$', consumers.AnomalyLogConsumer.as_asgi()),
]