from django.urls import re_path
from .src.consumers import TrainingConsumer

websocket_urlpatterns = [
    re_path(r"ws/train/$", TrainingConsumer.as_asgi()),
]