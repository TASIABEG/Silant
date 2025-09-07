from django.contrib.auth.decorators import user_passes_test
from functools import wraps
from django.http import HttpResponseForbidden

def role_required(roles):
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if request.user.is_authenticated and request.user.role in roles:
                return view_func(request, *args, **kwargs)
            return HttpResponseForbidden("Доступ запрещен")
        return wrapper
    return decorator