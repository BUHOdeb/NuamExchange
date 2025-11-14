# App/models.py
"""
Modelos del sistema NuamExchange
Define las estructuras de datos para usuarios, auditorías e históricos
"""
from django.db import models
from django.conf import settings
from django.utils import timezone
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.validators import RegexValidator
from django.core.exceptions import ValidationError
from django.contrib.auth.models import User


# ==================== VALIDADORES PERSONALIZADOS ====================

# Validador de teléfono: acepta formato internacional
# Ejemplo: +56912345678
phone_regex = RegexValidator(
    regex=r'^\+?1?\d{9,15}$',
    message="Formato de teléfono inválido. Use: +56912345678"
)

def validate_edad(value):
    """
    Valida que la edad esté en un rango válido (0-150 años)
    
    Args:
        value: Valor de edad a validar
    
    Raises:
        ValidationError: Si la edad no está en el rango
    """
    if value < 0 or value > 150:
        raise ValidationError('La edad debe estar entre 0 y 150 años')


def validate_email_domain(value):
    """
    Valida que el email no sea de dominios temporales bloqueados
    
    Args:
        value: Email a validar
    
    Raises:
        ValidationError: Si el dominio está bloqueado
    """
    # Lista de dominios temporales no permitidos
    dominios_bloqueados = [
        'tempmail.com', 
        'throwaway.email', 
        '10minutemail.com',
        'guerrillamail.com',
        'mailinator.com'
    ]
    
    try:
        domain = value.split('@')[1].lower()
        if domain in dominios_bloqueados:
            raise ValidationError('No se permiten emails temporales')
    except IndexError:
        raise ValidationError('Email inválido')


# ==================== MODELO USUARIO ====================

class Usuario(models.Model):
    """
    Modelo principal de Usuario del sistema
    
    IMPORTANTE: Este modelo NO se usa para autenticación (login/password)
    Para autenticación usar django.contrib.auth.models.User
    
    Este modelo almacena información adicional de usuarios del negocio
    """

    ROL_CHOICES = [
        ('ADMIN', 'administrador'),
        ('USER', 'Usuario'),
    ]
    
    user = models.OneToOneField(
        User,
        on_delete= models.CASCADE,
        null=True,
        blank=True,
    )


    # Nombre del usuario
    first_name = models.CharField(
        max_length=50,
        verbose_name='Nombre',
        help_text='Nombre del usuario'
    )
    
    # Apellido del usuario
    last_name = models.CharField(
        max_length=50,
        verbose_name='Apellido',
        help_text='Apellido del usuario'
    )
    
    # Edad del usuario (opcional)
    # PositiveIntegerField no permite números negativos automáticamente
    edad = models.PositiveIntegerField(
        null=True,
        blank=True,
        validators=[validate_edad],
        verbose_name='Edad',
        help_text='Edad en años (0-150)'
    )
    

    # Email único en el sistema
    # Se valida formato y dominio
    email = models.EmailField(
        max_length=254,
        unique=True,  # No puede haber dos usuarios con el mismo email
        validators=[validate_email_domain],
        verbose_name='Email',
        help_text='Correo electrónico único'
    )
    
    password = models.CharField(
        max_length=128,
        verbose_name='Password',
        help_text='Contraseña (minimo 6 caracteres)',
        null=True,
        )

    # Teléfono del usuario (opcional)
    # Valida formato internacional
    telefono = models.CharField(
        max_length=30,
        blank=True,
        null=True,
        unique=True,  # No puede haber dos usuarios con el mismo teléfono
        validators=[phone_regex],
        verbose_name='Teléfono',
        help_text='Formato: +56912345678'
    )
    
    # Fecha de nacimiento (opcional)
    fecha_nacimiento = models.DateField(
        null=True,
        blank=True,
        verbose_name='Fecha de Nacimiento'
    )

    # Asignacion de rol
    rol = models.CharField(max_length=55, choices=ROL_CHOICES, default='USER')
    
    # ===== CAMPOS DE AUDITORÍA =====
    
    # Fecha de creación del registro (se asigna automáticamente)
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Fecha de Creación'
    )
    
    # Fecha de última actualización (se actualiza automáticamente)
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='Última Actualización'
    )
    
    # Usuario que creó este registro
    # Si el usuario se elimina, este campo se pone en NULL
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='usuarios_creados',
        verbose_name='Creado Por'
    )
    
    # Soft delete: en lugar de eliminar, marcamos como inactivo
    is_active = models.BooleanField(
        default=True,
        verbose_name='Activo',
        help_text='Usuario activo en el sistema'
    )
    
    categoria = models.ForeignKey('categoria', on_delete=models.CASCADE, null = True)
    class Meta:
        # Ordenar por fecha de creación descendente (más recientes primero)
        ordering = ['-created_at']
        verbose_name = "Usuario"
        verbose_name_plural = "Usuarios"
        
        # Índices para mejorar rendimiento en búsquedas
        indexes = [
            models.Index(fields=['email']),
            models.Index(fields=['telefono']),
            models.Index(fields=['-created_at']),
        ]
    
    def __str__(self):
        """Representación en string del usuario"""
        return f"{self.first_name} {self.last_name} <{self.email}>"
    
    def clean(self):
        """
        Validaciones personalizadas antes de guardar
        Se ejecuta al llamar full_clean() o al guardar con validación
        """
        super().clean()
        
        # Normalizar email: convertir a minúsculas y quitar espacios
        if self.email:
            self.email = self.email.lower().strip()
        
        # Validar teléfono chileno
        if self.telefono:
            self.telefono = self.telefono.strip()
            # Verificar que empiece con +56 o 56
            if not self.telefono.startswith('+56') and not self.telefono.startswith('56'):
                raise ValidationError({
                    'telefono': 'El teléfono debe ser chileno (+56)'
                })
        
        # Validar fecha de nacimiento
        if self.fecha_nacimiento:
            from datetime import date
            
            # No puede ser fecha futura
            if self.fecha_nacimiento > date.today():
                raise ValidationError({
                    'fecha_nacimiento': 'La fecha no puede ser futura'
                })
            
            # Calcular edad automáticamente si no existe
            if not self.edad:
                today = date.today()
                self.edad = today.year - self.fecha_nacimiento.year - (
                    (today.month, today.day) < 
                    (self.fecha_nacimiento.month, self.fecha_nacimiento.day)
                )
    
    def save(self, *args, **kwargs):
        """
        Sobrescribir save para ejecutar validaciones
        """
        # Ejecutar validaciones antes de guardar
        self.full_clean()
        super().save(*args, **kwargs)

class Categoria(models.Model):
    name = models.CharField(max_length=50, null = True, blank=True)

    def __str__(self):
        return self.name


# ==================== MODELO AUDITORÍA DE IMPORTACIONES ====================

class ImportAudit(models.Model):
    """
    Auditoría de importaciones de archivos Excel
    Registra cada carga de archivo y su resultado
    """
    
    # Estados posibles de una importación
    STATUS_PENDING = 'PENDING'        # Archivo cargado, pendiente de validar
    STATUS_VALIDATED = 'VALIDATED'    # Archivo validado, listo para importar
    STATUS_IMPORTING = 'IMPORTING'    # Importación en proceso
    STATUS_IMPORTED = 'IMPORTED'      # Importación completada exitosamente
    STATUS_CANCELLED = 'CANCELLED'    # Importación cancelada por usuario
    STATUS_FAILED = 'FAILED'          # Importación falló
    
    STATUS_CHOICES = [
        (STATUS_PENDING, 'Pendiente revisión'),
        (STATUS_VALIDATED, 'Validado'),
        (STATUS_IMPORTING, 'Importando'),
        (STATUS_IMPORTED, 'Importado exitosamente'),
        (STATUS_CANCELLED, 'Cancelado'),
        (STATUS_FAILED, 'Falló'),
    ]
    
    # Usuario que subió el archivo
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name='Usuario'
    )
    
    # Fecha de carga del archivo
    uploaded_at = models.DateTimeField(
        default=timezone.now,
        verbose_name='Fecha de Carga'
    )
    
    # Archivo subido (se guarda en media/imports/YYYY/MM/)
    file = models.FileField(
        upload_to='imports/%Y/%m/',
        null=True,
        blank=True,
        verbose_name='Archivo'
    )
    
    # Nombre del archivo
    filename = models.CharField(
        max_length=255,
        blank=True,
        verbose_name='Nombre del Archivo'
    )
    
    # Estadísticas de la importación
    row_count = models.PositiveIntegerField(
        default=0,
        verbose_name='Total de Filas',
        help_text='Total de filas en el archivo'
    )
    
    imported_count = models.PositiveIntegerField(
        default=0,
        verbose_name='Registros Creados',
        help_text='Cantidad de usuarios nuevos creados'
    )
    
    updated_count = models.PositiveIntegerField(
        default=0,
        verbose_name='Registros Actualizados',
        help_text='Cantidad de usuarios existentes actualizados'
    )
    
    error_count = models.PositiveIntegerField(
        default=0,
        verbose_name='Errores',
        help_text='Cantidad de filas con errores'
    )
    
    # Lista de errores en formato JSON
    # Ejemplo: [{"row": 5, "errors": ["Email inválido"]}, ...]
    errors = models.JSONField(
        default=list,
        blank=True,
        verbose_name='Detalle de Errores'
    )
    
    # Estado actual de la importación
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=STATUS_PENDING,
        verbose_name='Estado'
    )
    
    # Tiempo que tomó procesar el archivo
    processing_time = models.DurationField(
        null=True,
        blank=True,
        verbose_name='Tiempo de Procesamiento'
    )
    
    class Meta:
        ordering = ['-uploaded_at']
        verbose_name = "Auditoría de Importación"
        verbose_name_plural = "Auditorías de Importaciones"
    
    def __str__(self):
        return f"Import {self.id} - {self.status} - {self.uploaded_at.date()}"


# ==================== MODELO HISTÓRICO DE USUARIOS ====================

class UsuarioHistorico(models.Model):
    """
    Histórico de cambios en usuarios
    Guarda una copia de los datos cada vez que se modifica un usuario
    """
    
    # Usuario al que pertenece este histórico
    usuario = models.ForeignKey(
        Usuario,
        on_delete=models.CASCADE,  # Si se elimina el usuario, se eliminan sus históricos
        related_name='historicos',
        verbose_name='Usuario'
    )
    
    # Datos históricos (copia del estado anterior)
    first_name = models.CharField(max_length=100, verbose_name='Nombre')
    last_name = models.CharField(max_length=100, verbose_name='Apellido')
    edad = models.PositiveIntegerField(null=True, blank=True, verbose_name='Edad')
    email = models.EmailField(max_length=254, verbose_name='Email')
    telefono = models.CharField(max_length=30, blank=True, null=True, verbose_name='Teléfono')
    fecha_nacimiento = models.DateField(null=True, blank=True, verbose_name='Fecha Nacimiento')
    
    # Fecha de modificación
    modified_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Fecha de Modificación'
    )
    
    # Usuario que hizo la modificación
    modified_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name='Modificado Por'
    )
    
    # Razón del cambio (opcional)
    change_reason = models.TextField(
        blank=True,
        null=True,
        verbose_name='Razón del Cambio'
    )
    
    class Meta:
        ordering = ['-modified_at']
        verbose_name = "Histórico de Usuario"
        verbose_name_plural = "Históricos de Usuarios"
    
    def __str__(self):
        return f"Histórico de {self.usuario} - {self.modified_at}"


# ==================== MODELO PERFIL DE USUARIO (ROLES) ====================

class UserProfile(models.Model):
    """
    Perfil extendido para el sistema de roles
    Se relaciona uno-a-uno con django.contrib.auth.models.User
    """
    
    # Opciones de roles en el sistema
    ROLE_CHOICES = [
        ('Admin', 'Administrador'),      # Acceso completo al sistema
        ('Manager', 'Gerente'),          # Puede gestionar usuarios
        ('Employee', 'Empleado'),        # Acceso básico
    ]
    
    # Relación uno a uno con User de Django
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='profile',
        verbose_name='Usuario'
    )
    
    # Rol del usuario en el sistema
    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES,
        default='Employee',
        verbose_name='Rol'
    )
    
    # Teléfono del perfil
    phone = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        verbose_name='Teléfono'
    )
    
    # Departamento al que pertenece
    department = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name='Departamento'
    )
    
    # Fecha de contratación
    hire_date = models.DateField(
        auto_now_add=True,
        verbose_name='Fecha de Contratación'
    )
    
    # Avatar del usuario (opcional)
    avatar = models.ImageField(
        upload_to='avatars/',
        blank=True,
        null=True,
        verbose_name='Avatar'
    )
    
    # Si el usuario está verificado
    is_verified = models.BooleanField(
        default=False,
        verbose_name='Verificado'
    )
    
    def __str__(self):
        return f"{self.user.username} - {self.role}"
    
    class Meta:
        verbose_name = 'Perfil de Usuario'
        verbose_name_plural = 'Perfiles de Usuarios'


# ==================== SEÑALES (SIGNALS) ====================

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """
    Señal: Crear perfil automáticamente cuando se crea un User
    
    Args:
        sender: Modelo que envió la señal (User)
        instance: Instancia del User creado
        created: True si es un nuevo registro
    """
    if created:
        UserProfile.objects.create(user=instance)


@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    """
    Señal: Guardar perfil cuando se guarda un User
    
    Args:
        sender: Modelo que envió la señal (User)
        instance: Instancia del User guardado
    """
    # Verificar que el perfil existe antes de guardarlo
    if hasattr(instance, 'profile'):
        instance.profile.save()


@receiver(post_save, sender=Usuario)
def create_autenticado(sender, instance, created, **kwargs):
    if created and instance.email:
        user = User.objects.create_user(
            username=instance.email,
            email=instance.email,
            password="1234"
        )

        Usuario.objects.filter(id=instance.id).update(user=user)

@receiver(post_save, sender=Usuario)
def create_usuario_historico(sender, instance, created, **kwargs):
    """
    Señal: Crear histórico cada vez que se actualiza un usuario
    NO se crea histórico cuando es un nuevo usuario
    
    Args:
        sender: Modelo que envió la señal (Usuario)
        instance: Instancia del Usuario guardado
        created: True si es un nuevo registro
    """
    # Solo crear histórico para actualizaciones (no para nuevos registros)
    if not created:
        UsuarioHistorico.objects.create(
            usuario=instance,
            first_name=instance.first_name,
            last_name=instance.last_name,
            edad=instance.edad,
            email=instance.email,
            telefono=instance.telefono,
            fecha_nacimiento=instance.fecha_nacimiento
        )
# App/models.py