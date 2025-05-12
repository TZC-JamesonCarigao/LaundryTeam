import os
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
import scheduler.routing

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'wifischeduler.settings')

application = ProtocolTypeRouter({
    "http": get_asgi_application(),
    "websocket": AuthMiddlewareStack(
        URLRouter(
            scheduler.routing.websocket_urlpatterns
        )
    ),
})