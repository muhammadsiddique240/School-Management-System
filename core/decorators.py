from django.http import HttpResponseForbidden
from django.shortcuts import redirect
from functools import wraps


def role_required(*roles):
    """Decorator that restricts view access to users with specific roles."""
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect('login')
            if request.user.role not in roles and not request.user.is_superuser:
                return HttpResponseForbidden(
                    '<div style="text-align:center;margin-top:100px;font-family:sans-serif;">'
                    '<h1>403 - Access Denied</h1>'
                    '<p>You do not have permission to access this page.</p>'
                    f'<p>Required role(s): {", ".join(roles)}</p>'
                    '<a href="/" style="color:#764ba2;">Go to Dashboard</a>'
                    '</div>'
                )
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator
