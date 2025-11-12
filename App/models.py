# App/models.py - MEJORADO
from django.db import models
from django.conf import settings
from django.utils import timezone
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.validators import MinValueValidator, MaxValueValidator, RegexValidator
from django.core.exceptions import ValidationError
import re

'''
Validadores personalizados en formato estandar 
para evitar incongruencia en la base de datos y por ende sea masconfiable nuestro nucleo de verdad
'''
phone_regex = RegexValidator(
    regex=r'^\+?1?\d{9,15}$',
    message="Formato de teléfono inválido. Use: +56912345678"
)

def validate_edad(value):
    if value < 0 or value > 150:
        raise ValidationError('La edad debe estar entre 0 y 150 años')

def validate_email_domain(value):
    """Validar que el email no sea de dominios temporales"""
    dominios_bloqueados = ['tempmail.com', 'throwaway.email', '10minutemail.com']
    domain = value.split('@')[1].lower()
    if domain in dominios_bloqueados:
        raise ValidationError('No se permiten emails temporales')

class Usuario(models.Model):
    """
    Modelo de Usuario del sistema - NO usar para autenticación
    Usar django.contrib.auth.models.User para login 
    """
    first_name = models.CharField(
        max_length=50,
        verbose_name='Nombre',
        help_text='Nombre del usuario'
    )
    
    last_name = models.CharField(
        max_length=50,
        verbose_name='Apellido',
        help_text='Apellido del usuario'
    )
    
    edad = models.PositiveIntegerField(
        null=True,
        blank=True,
        validators=[validate_edad],
        verbose_name='Edad',
        help_text='Edad en años (0-150)'
    )
    
    email = models.EmailField(
        max_length=254,
        unique=True,
        validators=[validate_email_domain],
        verbose_name='Email',
        help_text='Correo electrónico único'
    )
    
    telefono = models.CharField(
        max_length=30,
        blank=True,
        null=True,
        unique=True,
        validators=[phone_regex],
        verbose_name='Teléfono',
        help_text='Formato: +56912345678'
    )
    
    fecha_nacimiento = models.DateField(
        null=True,
        blank=True,
        verbose_name='Fecha de Nacimiento'
    )
    
    # ELIMINAR password_hash - NO NECESARIO
    # Django ya tiene User con contraseñas seguras
    
    # Campos de auditoría
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='usuarios_creados'
    )
    is_active = models.BooleanField(default=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = "Usuario"
        verbose_name_plural = "Usuarios"
        indexes = [
            models.Index(fields=['email']),
            models.Index(fields=['telefono']),
            models.Index(fields=['-created_at']),
        ]
    
    def __str__(self):
        return f"{self.first_name} {self.last_name} <{self.email}>"
    
    def clean(self):
        """Validaciones personalizadas"""
        super().clean()
        
        # Normalizar email
        if self.email:
            self.email = self.email.lower().strip()
        
        # Validar teléfono chileno
        if self.telefono:
            self.telefono = self.telefono.strip()
            if not self.telefono.startswith('+56') and not self.telefono.startswith('56'):
                raise ValidationError({'telefono': 'El teléfono debe ser chileno (+56)'})
        
        # Validar fecha de nacimiento
        if self.fecha_nacimiento:
            from datetime import date
            if self.fecha_nacimiento > date.today():
                raise ValidationError({'fecha_nacimiento': 'La fecha no puede ser futura'})
            
            # Calcular edad automáticamente si no existe
            if not self.edad:
                today = date.today()
                self.edad = today.year - self.fecha_nacimiento.year - (
                    (today.month, today.day) < (self.fecha_nacimiento.month, self.fecha_nacimiento.day)
                )
    
    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)


class ImportAudit(models.Model):
    """Auditoría de importaciones Excel"""
    STATUS_PENDING = 'PENDING'
    STATUS_VALIDATED = 'VALIDATED'
    STATUS_IMPORTING = 'IMPORTING'
    STATUS_IMPORTED = 'IMPORTED'
    STATUS_CANCELLED = 'CANCELLED'
    STATUS_FAILED = 'FAILED'
    
    STATUS_CHOICES = [
        (STATUS_PENDING, 'Pendiente revisión'),
        (STATUS_VALIDATED, 'Validado'),
        (STATUS_IMPORTING, 'Importando'),
        (STATUS_IMPORTED, 'Importado exitosamente'),
        (STATUS_CANCELLED, 'Cancelado'),
        (STATUS_FAILED, 'Falló'),
    ]
    
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name='Usuario'
    )
    
    uploaded_at = models.DateTimeField(default=timezone.now)
    
    file = models.FileField(upload_to='imports/%Y/%m/', null=True, blank=True)
    
    filename = models.CharField(max_length=255, blank=True)
    
    row_count = models.PositiveIntegerField(default=0)
    
    imported_count = models.PositiveIntegerField(default=0)
    
    updated_count = models.PositiveIntegerField(default=0)
    
    error_count = models.PositiveIntegerField(default=0)
    
    errors = models.JSONField(default=list, blank=True)
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDING)
    
    processing_time = models.DurationField(null=True, blank=True)
    
    class Meta:
        ordering = ['-uploaded_at']
        verbose_name = "Auditoría de Importación"
        verbose_name_plural = "Auditorías de Importaciones"
    
    def __str__(self):
        return f"Import {self.id} - {self.status} - {self.uploaded_at.date()}"


class UsuarioHistorico(models.Model):
    """Histórico de cambios en usuarios"""
    usuario = models.ForeignKey(
        Usuario,
        on_delete=models.CASCADE,
        related_name='historicos'
    )
    
    first_name = models.CharField(max_length=100)
    
    last_name = models.CharField(max_length=100)
    
    edad = models.PositiveIntegerField(null=True, blank=True)
    
    email = models.EmailField(max_length=254)
    
    telefono = models.CharField(max_length=30, blank=True, null=True)
    
    fecha_nacimiento = models.DateField(null=True, blank=True)
    
    modified_at = models.DateTimeField(auto_now_add=True)
    
    modified_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    change_reason = models.TextField(blank=True, null=True)
    
    class Meta:
        ordering = ['-modified_at']
        verbose_name = "Histórico de Usuario"
        verbose_name_plural = "Históricos de Usuarios"
    
    def __str__(self):
        return f"Histórico de {self.usuario} - {self.modified_at}"


class UserProfile(models.Model):
    """Perfil extendido para sistema de roles"""
    ROLE_CHOICES = [
        ('Admin', 'Administrador'),
        ('Manager', 'Gerente'),
        ('Employee', 'Empleado'),
    ]
    
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='profile'
    )
    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES,
        default='Employee'
    )
    phone = models.CharField(max_length=20, blank=True, null=True)
    department = models.CharField(max_length=100, blank=True, null=True)
    hire_date = models.DateField(auto_now_add=True)
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True)
    is_verified = models.BooleanField(default=False)
    
    def __str__(self):
        return f"{self.user.username} - {self.role}"
    
    class Meta:
        verbose_name = 'Perfil de Usuario'
        verbose_name_plural = 'Perfiles de Usuarios'


# Signals
@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    if hasattr(instance, 'profile'):
        instance.profile.save()

@receiver(post_save, sender=Usuario)
def create_usuario_historico(sender, instance, created, **kwargs):
    """Crear histórico cada vez que se modifica un usuario"""
    if not created:  # Solo para actualizaciones
        UsuarioHistorico.objects.create(
            usuario=instance,
            first_name=instance.first_name,
            last_name=instance.last_name,
            edad=instance.edad,
            email=instance.email,
            telefono=instance.telefono,
            fecha_nacimiento=instance.fecha_nacimiento
        )