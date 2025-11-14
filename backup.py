from datetime import date
from pyexpat.errors import messages

from django.shortcuts import get_object_or_404, redirect, render
from App.forms import UsuarioForm,Usuario
from django.contrib.auth.decorators import login_required

@login_required
def editar_usuario(request, usuario_id):
    # ... (código de permisos)
    usuario = get_object_or_404(Usuario, id=usuario_id)
    if request.method == 'POST':
        # 1. Instanciar el formulario con los datos POST y la instancia del usuario
        form = UsuarioForm(request.POST, instance=usuario)

        if form.is_valid():
            # 2. Guardar los datos limpios y validados
            form.save()

            # 3. Manejo opcional de la contraseña
            nueva_password = request.POST.get('password', '')
            if nueva_password:
                 usuario.set_password(nueva_password)
                 usuario.save(update_fields=['password']) # Solo guardar la contraseña

            messages.success(request, "Usuario actualizado exitosamente :D.")
            return redirect('listar_usuarios')
        else:
            # 3. Si no es válido, re-renderizar la plantilla con los errores
            messages.error(request, "Por favor, corrige los errores en el formulario.")
            return render(request, 'editar.html', {
                'usuario': usuario,
                'errors': form.errors # Se usa 'form.errors' en lugar de 'errors'
            })

    # views.py (Parte del Método GET)

    else: # Método GET
        # 4. En GET, usa el formulario para pre-cargar los datos
        form = UsuarioForm(instance=usuario)

        return render(request, 'editar.html', {
            'usuario': usuario,
            'today': date.today(), # Agrega 'today' si lo usas para el campo fecha_nacimiento
            # Si quieres usar el ModelForm para renderizar campos
            # 'form': form 
        })
    # Aquí es donde DEBE volver a renderizar en caso de error en POST
    return render(request, 'editar.html', {'usuario': usuario, 'today': date.today()})



