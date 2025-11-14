# app/decorators.py
from functools import wraps
from django.shortcuts import redirect
from django.contrib import messages

def admin_required(view_func):
    """
    Decorador para permitir acceso solo a usuarios con rol 'admin'.
    Redirige a 'home' con mensaje si no es admin.
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        # Intentar obtener el rol del perfil, manejar si no existe
        role = getattr(getattr(request.user, 'profile', None), 'role', '').lower()
        
        if role == 'admin':
            return view_func(request, *args, **kwargs)
        
        # Si no tiene permisos, mostrar mensaje y redirigir
        messages.error(request, "No tienes permisos para acceder a esta página.")
        return redirect('home')  # Cambiar 'home' por la URL de tu página principal
    return wrapper
