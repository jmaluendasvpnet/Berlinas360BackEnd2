# mysite/asgi.py

import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
django.setup()
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from myapp.consumers import SessionConsumer, NotificationConsumer, SiniestroConsumer
from django.urls import path


application = ProtocolTypeRouter({
    "http": get_asgi_application(),
    "websocket": AuthMiddlewareStack(
        URLRouter([
            path('ws/sessions/', SessionConsumer.as_asgi()),
            path('ws/notifications/', NotificationConsumer.as_asgi()),
            path('ws/siniestros/<siniestro_id>/', SiniestroConsumer.as_asgi()),
        ])
    ),
})
