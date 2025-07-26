# myapp/middleware.py
import threading
from django.contrib.auth.models import AnonymousUser # Ensure this is imported if you return it

_thread_locals = threading.local()

def get_current_request():
    """
    Retrieves the current request object from thread-local storage.
    """
    return getattr(_thread_locals, "request", None)

def get_current_user():
    """
    Retrieves the authenticated user from the current request in thread-local storage.
    Returns None if the request or user is not available or not authenticated.
    """
    request = get_current_request()
    if request and hasattr(request, 'user') and request.user.is_authenticated:
        return request.user
    # Optionally, you could return AnonymousUser() if your signals expect a user object
    # return AnonymousUser()
    return None

class CurrentUserMiddleware:
    """
    Middleware to store the current request object in thread-local storage.
    This allows access to the request (and thus the authenticated user)
    from anywhere in the code during the request's lifecycle, like in signal handlers.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        _thread_locals.request = request # Store the entire request object
        response = self.get_response(request)
        # Clean up the thread-local variable after the response is generated
        if hasattr(_thread_locals, 'request'):
            del _thread_locals.request
        return response

# Your JWTAuthMiddleware and get_user_from_token for Channels would remain the same
# as they serve a different purpose (WebSocket authentication).
# from django.contrib.auth.models import AnonymousUser # Already at the top
from django.conf import settings
from channels.db import database_sync_to_async
from django.contrib.auth import get_user_model
import jwt

@database_sync_to_async
def get_user_from_token(token):
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=['HS256'])
        # Ensure your Login model uses 'username' as expected by this JWT payload
        user = get_user_model().objects.get(username=payload['username'])
        return user
    except Exception as e:
        return AnonymousUser()

class JWTAuthMiddleware:
    def __init__(self, inner):
        self.inner = inner

    def __call__(self, scope):
        return JWTAuthMiddlewareInstance(scope, self)

class JWTAuthMiddlewareInstance:
    def __init__(self, scope, middleware):
        self.scope = scope
        self.inner = middleware.inner

    async def __call__(self, receive, send):
        query_string = self.scope['query_string'].decode()
        query_params = dict(qc.split('=') for qc in query_string.split('&') if '=' in qc)
        token = query_params.get('token', None)

        if token:
            self.scope['user'] = await get_user_from_token(token)
        else:
            self.scope['user'] = AnonymousUser()
        
        return await self.inner(self.scope, receive, send)