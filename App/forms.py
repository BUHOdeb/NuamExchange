from django import forms
from .models import Usuario

class UsuarioForm(forms.ModelForm):
    password = forms.CharField(
        label = "contraseña",
        max_length=128,
        widget=forms.PasswordInput
    )

    class Meta:
        model = Usuario
        fields = [
            'first_name',
            'last_name',
            'email',
            'edad',
            'telefono',
            'fecha_nacimiento'
        ]