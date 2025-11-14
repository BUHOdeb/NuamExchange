from django import forms
from .models import Usuario

class UsuarioForm(forms.ModelForm):
    # Campo de contraseña opcional, ya que solo se debe cambiar si el usuario lo desea.
    password = forms.CharField(
        label='Nueva Contraseña',
        required=False,
        widget=forms.PasswordInput(attrs={'placeholder': 'Dejar en blanco para no cambiar'})
    )

    class Meta:
        model = Usuario
        # Incluye todos los campos de tu template que deben ser editables
        fields = [
            'first_name', 'last_name', 'email', 'telefono', 
            'edad', 'fecha_nacimiento', 'rol', 'is_active'
        ]
        # Si usas el User de Django para login, el campo 'user' no debería estar aquí.
        # Si quieres que el campo 'categoria' sea editable, agrégalo a la lista de fields.

    def clean_telefono(self):
        # Limpieza personalizada para evitar que se lance un error de unicidad
        # si el usuario no cambia su propio teléfono.
        telefono = self.cleaned_data.get('telefono')
        if telefono:
            # Busca otros usuarios con ese teléfono, excluyendo el usuario actual (instancia)
            if Usuario.objects.filter(telefono=telefono).exclude(pk=self.instance.pk).exists():
                raise forms.ValidationError("Este número de teléfono ya está registrado por otro usuario.")
        return telefono
        
    def clean_email(self):
        # Limpieza personalizada para evitar que se lance un error de unicidad
        # si el usuario no cambia su propio email.
        email = self.cleaned_data.get('email')
        if email:
            # Normalizar el email como lo hace tu modelo antes de buscar
            email_normalized = email.lower().strip()
            # Busca otros usuarios con ese email, excluyendo el usuario actual (instancia)
            if Usuario.objects.filter(email=email_normalized).exclude(pk=self.instance.pk).exists():
                raise forms.ValidationError("Este correo electrónico ya está registrado por otro usuario.")
        return email

    def save(self, commit=True):
        # Sobreescribir save para evitar que la contraseña se guarde como texto plano
        instance = super().save(commit=False)
        # El manejo de la contraseña lo dejas en la vista (editar_usuario)
        if commit:
            instance.save()
        return instance