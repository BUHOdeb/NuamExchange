# miapp/models.py
from django.db import models
from django.conf import settings
from django.utils import timezone

class Usuario(models.Model):
    
    first_name = models.CharField(max_length=100)
    sas_name = models.CharField(max_length=100)

    last_name = models.CharField(max_length=100)
    
    # El siguiente formato esta asi porque no se puede tener numero negativos no mamen
    edad = models.PositiveIntegerField(null=True, blank=True) 
    
    email = models.EmailField(max_length=254, unique=True)
    
    telefono = models.CharField(max_length=30, blank=True, null=True, unique=True)

    fecha_nacimiento = models.DateField(null=True, blank=True)

    class Meta:
        ordering = ['-edad', 'first_name'] #edad en negativo pa que sea descendente
        verbose_name = "Usuario"
        verbose_name_plural = "Usuarios"

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

