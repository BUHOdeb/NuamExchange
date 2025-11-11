# miapp/models.py
from django.db import models
from django.conf import settings
from django.utils import timezone
from django.contrib.auth.hashers import make_password, check_password

class Usuario(models.Model):
    
    first_name = models.CharField(max_length=50)

    last_name = models.CharField(max_length=50)
    
    # El siguiente formato esta asi porque no se puede tener numero negativos no mamen
    edad = models.PositiveIntegerField(null=True, blank=True) 
    
    email = models.EmailField(max_length=254, unique=True)
    
    telefono = models.CharField(max_length=30, blank=True, null=True, unique=True)

    fecha_nacimiento = models.DateField(null=True, blank=True)

    password_hash = models.CharField(max_length=30, null=True, blank=True)    

    def set_clave_secreta(self, clave_raw):
        self.clave_secreta_hash = make_password(clave_raw)
    
    def check_clave_secreta(self, clave_raw):
        return check_password(clave_raw, self.clave_secreta_hash)

    class Meta:
        
        ordering = ['-edad', 'first_name'] #edad en negativo pa que sea descendente
        # verbose_name = "Usuario"
        # verbose_name_plural = "Usuarios"

    def __str__(self):
        return f"{self.first_name} {self.last_name} <{self.email}>"

class ImportAudit(models.Model):
   
    STATUS_PENDING = 'PENDING'
   
    STATUS_VALIDATED = 'VALIDATED'
    
    STATUS_IMPORTING = 'IMPORTING'
    
    STATUS_IMPORTED = 'IMPORTED'
    
    STATUS_CANCELLED = 'CANCELLED'
    
    STATUS_FAILED = 'FAILED'

    STATUS_CHOICES = [
        
        (STATUS_PENDING, 'Pendiente revisión'),
        
        (STATUS_VALIDATED, 'Validado (en espera de confirmación)'),
        
        (STATUS_IMPORTING, 'Importando'),
        
        (STATUS_IMPORTED, 'Importado'),

        (STATUS_CANCELLED, 'Cancelado'),

        (STATUS_FAILED, 'Falló'),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    
    uploaded_at = models.DateTimeField(default=timezone.now)
    
    file = models.FileField(upload_to='imports/', null=True, blank=True)
    
    filename = models.CharField(max_length=255, blank=True)
    
    row_count = models.PositiveIntegerField(default=0)
    
    imported_count = models.PositiveIntegerField(default=0)
    
    updated_count = models.PositiveIntegerField(default=0)
    error_count = models.PositiveIntegerField(default=0)

    errors = models.JSONField(default=list, blank=True)  # lista de {row: int, errors: [..]}

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDING)

    class Meta:
        ordering = ['-uploaded_at']

    def __str__(self):
        return f"Import {self.id} by {self.user} on {self.uploaded_at.date()} ({self.status})"
    
class UsuarioHistorico(models.Model):
    usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE, related_name='historicos')
    
    first_name = models.CharField(max_length=100)
    
    last_name = models.CharField(max_length=100)
    
    edad = models.PositiveIntegerField(null=True, blank=True)
    
    email = models.EmailField(max_length=254)
    
    telefono = models.CharField(max_length=30, blank=True, null=True)
    
    
    fecha_nacimiento = models.DateField(null=True, blank=True)
    modified_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-modified_at']
        verbose_name = "Histórico de Usuario"
        verbose_name_plural = "Históricos de Usuarios"

    def __str__(self):
        return f"Histórico de {self.usuario} modificado en {self.modified_at}"