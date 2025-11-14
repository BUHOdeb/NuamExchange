# App/decorators.py - NUEVO ARCHIVO
from django.shortcuts import redirect
from django.contrib import messages
from functools import wraps

def role_required(role_names):
    """
    Decorador para verificar roles
    Uso: @role_required(['Admin', 'Manager'])
    """
    if isinstance(role_names, str):
        role_names = [role_names]
    
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if not request.user.is_authenticated:
                messages.warning(request, 'Debes iniciar sesión')
                return redirect('login')
            
            user_groups = request.user.groups.values_list('name', flat=True)
            
            if any(role in user_groups for role in role_names):
                return view_func(request, *args, **kwargs)
            else:
                messages.error(request, 'No tienes permisos para acceder a esta sección')
                return redirect('home')
        return wrapper
    return decorator

# Decoradores específicos
admin_required = role_required('Admin')
manager_required = role_required(['Admin', 'Manager'])
employee_required = role_required(['Admin', 'Manager', 'Employee'])