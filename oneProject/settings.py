# oneProject/settings.py
"""
Configuración de Django para el proyecto NuamExchange

SEGURIDAD:
- En producción usar variables de entorno
- Nunca compartir SECRET_KEY
- Cambiar DEBUG a False en producción
"""

import os
from pathlib import Path


# ==================== PATHS ====================

# Build paths inside the project like this: BASE_DIR / 'subdir'
# BASE_DIR apunta a la carpeta raíz del proyecto
BASE_DIR = Path(__file__).resolve().parent.parent


# ==================== SEGURIDAD ====================

# SECRET_KEY: Llave secreta para firmar cookies y tokens
# IMPORTANTE: En producción usar variable de entorno
# Generar nueva key: python -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())'
SECRET_KEY = os.environ.get(
    'SECRET_KEY',
    'django-insecure-!=+^t@e-3f)^xulrfazmkkp0k7f!sqpdbz$#=t8xuo5vr)%w8$'
)

# DEBUG: Modo de desarrollo
# True = Muestra errores detallados (NUNCA en producción)
# False = Muestra páginas de error genéricas
DEBUG = os.environ.get('DEBUG', 'True') == 'True'

# ALLOWED_HOSTS: Dominios permitidos para acceder al sitio
# En desarrollo: ['localhost', '127.0.0.1']
# En producción: ['tudominio.com', 'www.tudominio.com']
ALLOWED_HOSTS = os.environ.get(
    'ALLOWED_HOSTS',
    'localhost,127.0.0.1'
).split(',')


# ==================== APLICACIONES ====================

# Aplicaciones instaladas en el proyecto
# django.contrib.*: Aplicaciones core de Django
# App: Tu aplicación personalizada
INSTALLED_APPS = [
    'django.contrib.admin',          # Panel de administración
    'django.contrib.auth',           # Sistema de autenticación
    'django.contrib.contenttypes',   # Sistema de tipos de contenido
    'django.contrib.sessions',       # Manejo de sesiones
    'django.contrib.messages',       # Framework de mensajes
    'django.contrib.staticfiles',    # Manejo de archivos estáticos
    'App',                           # Tu aplicación
]


# ==================== MIDDLEWARE ====================

# Middleware: Procesa requests/responses en orden
# Se ejecutan de arriba hacia abajo en request
# Se ejecutan de abajo hacia arriba en response
MIDDLEWARE = [
    # Seguridad: Headers de seguridad HTTP
    'django.middleware.security.SecurityMiddleware',
    
    # Sesiones: Manejo de sesiones de usuario
    'django.contrib.sessions.middleware.SessionMiddleware',
    
    # Common: Redirecciones, ETags, etc.
    'django.middleware.common.CommonMiddleware',
    
    # CSRF: Protección contra Cross-Site Request Forgery
    'django.middleware.csrf.CsrfViewMiddleware',
    
    # Auth: Asocia usuarios con requests
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    
    # Messages: Sistema de mensajes flash
    'django.contrib.messages.middleware.MessageMiddleware',
    
    # Clickjacking: Protección contra clickjacking
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    
    # Custom: Middleware personalizado para prevenir caché
    #'App.middleware.NoCacheMiddleware', MODIFICADO
]


# ==================== URLs Y WSGI ====================

# Archivo raíz de URLs
ROOT_URLCONF = 'oneProject.urls'

# Aplicación WSGI para producción
WSGI_APPLICATION = 'oneProject.wsgi.application'


# ==================== TEMPLATES ====================

# Configuración de templates (HTML)
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        
        # Directorios donde buscar templates
        # Busca en App/templates/
        'DIRS': [BASE_DIR / 'App' / 'templates'],
        
        # Buscar templates dentro de cada app instalada
        'APP_DIRS': True,
        
        'OPTIONS': {
            # Context processors: Variables disponibles en todos los templates
            'context_processors': [
                'django.template.context_processors.debug',     # Variable debug
                'django.template.context_processors.request',   # Variable request
                'django.contrib.auth.context_processors.auth',  # Variable user
                'django.contrib.messages.context_processors.messages',  # Messages
            ],
        },
    },
]


# ==================== BASE DE DATOS ====================

# Configuración de PostgreSQL
# En producción usar variables de entorno para credenciales
DATABASES = {
    'default': {
        # Motor de base de datos
        'ENGINE': 'django.db.backends.postgresql',
        
        # Nombre de la base de datos
        'NAME': os.environ.get('DB_NAME', 'postgres'),
        
        # Usuario de PostgreSQL
        'USER': os.environ.get('DB_USER', 'postgres'),
        
        # Contraseña (USAR VARIABLE DE ENTORNO EN PRODUCCIÓN)
        'PASSWORD': os.environ.get('DB_PASSWORD', 'Admin123'),
        
        # Host: localhost en desarrollo
        'HOST': os.environ.get('DB_HOST', 'localhost'),
        
        # Puerto: 5432 es el puerto por defecto de PostgreSQL
        'PORT': os.environ.get('DB_PORT', '5432'),
        
        # Opciones adicionales
        'OPTIONS': {
            'connect_timeout': 10,  # Timeout de conexión en segundos
        },
        
        # Mantener conexiones abiertas (mejora rendimiento)
        'CONN_MAX_AGE': 600,  # 10 minutos
    }
}


# ==================== VALIDACIÓN DE CONTRASEÑAS ====================

# Validadores para contraseñas de usuarios
# Asegura que las contraseñas sean seguras
AUTH_PASSWORD_VALIDATORS = [
    {
        # No puede ser similar a información del usuario
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        # Longitud mínima de 8 caracteres
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
        'OPTIONS': {
            'min_length': 8,
        }
    },
    {
        # No puede ser contraseña común
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        # No puede ser solo números
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# ==================== INTERNACIONALIZACIÓN ====================

# Idioma: Español de Chile
LANGUAGE_CODE = 'es-cl'

# Zona horaria: Santiago de Chile
TIME_ZONE = 'America/Santiago'

# Habilitar internacionalización
USE_I18N = True

# Usar zonas horarias (recomendado)
USE_TZ = True


# ==================== ARCHIVOS ESTÁTICOS ====================

# URL para acceder a archivos estáticos (CSS, JS, imágenes)
STATIC_URL = '/static/'

# Directorio donde se recopilan los estáticos en producción
# Usar: python manage.py collectstatic
STATIC_ROOT = BASE_DIR / 'staticfiles'

# Directorios adicionales con archivos estáticos
STATICFILES_DIRS = [
    BASE_DIR / 'App' / 'static',
]


# ==================== ARCHIVOS DE MEDIA ====================

# URL para acceder a archivos subidos por usuarios
MEDIA_URL = '/media/'

# Directorio donde se guardan archivos subidos
MEDIA_ROOT = BASE_DIR / 'media'


# ==================== CONFIGURACIÓN DE AUTENTICACIÓN ====================

# URLs de autenticación
LOGIN_URL = 'login'
LOGIN_REDIRECT_URL = 'home'
LOGOUT_REDIRECT_URL = 'login'



# ==================== CONFIGURACIÓN DE SESIONES ====================

# Duración de la sesión: 24 horas (en segundos)
SESSION_COOKIE_AGE = 86400

# Usar HTTPS solo en cookies de sesión (True en producción)
SESSION_COOKIE_SECURE = not DEBUG

# No accesible desde JavaScript (seguridad)
SESSION_COOKIE_HTTPONLY = True

# Protección CSRF
SESSION_COOKIE_SAMESITE = 'Lax'


# ==================== CONFIGURACIÓN DE CSRF ====================

# Cookies CSRF solo por HTTPS en producción
CSRF_COOKIE_SECURE = not DEBUG

# No accesible desde JavaScript
CSRF_COOKIE_HTTPONLY = True

# Protección adicional
CSRF_COOKIE_SAMESITE = 'Lax'


# ==================== SEGURIDAD ADICIONAL (PRODUCCIÓN) ====================

if not DEBUG:
    # Redirigir todo a HTTPS
    SECURE_SSL_REDIRECT = True
    
    # HTTP Strict Transport Security: 1 año
    SECURE_HSTS_SECONDS = 31536000
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
    
    # No permitir sniffing de content-type
    SECURE_CONTENT_TYPE_NOSNIFF = True
    
    # Protección XSS en navegadores viejos
    SECURE_BROWSER_XSS_FILTER = True
    
    # No permitir iframe (clickjacking)
    X_FRAME_OPTIONS = 'DENY'


# ==================== LOGGING ====================

# Configuración de logs para debugging y auditoría
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    
    # Formatos de log
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {message}',
            'style': '{',
        },
    },
    
    # Handlers: donde se escriben los logs
    'handlers': {
        # Archivo rotativo (máximo 10MB, 5 archivos)
        'file': {
            'level': 'INFO',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': BASE_DIR / 'logs' / 'django.log',
            'maxBytes': 1024 * 1024 * 10,  # 10MB
            'backupCount': 5,
            'formatter': 'verbose',
        },
        # Consola (terminal)
        'console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
    },
    
    # Loggers: qué se registra
    'loggers': {
        # Logs de Django
        'django': {
            'handlers': ['file', 'console'],
            'level': 'INFO',
            'propagate': False,
        },
        # Logs de tu aplicación
        'App': {
            'handlers': ['file', 'console'],
            'level': 'INFO',
            'propagate': False,
        },
    },
}

# Crear carpeta de logs si no existe
os.makedirs(BASE_DIR / 'logs', exist_ok=True)


# ==================== EMAIL ====================

# Backend de email para desarrollo (imprime en consola)
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# Para producción con SMTP (descomenta y configura):
# EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
# EMAIL_HOST = 'smtp.gmail.com'
# EMAIL_PORT = 587
# EMAIL_USE_TLS = True
# EMAIL_HOST_USER = os.environ.get('EMAIL_USER')
# EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_PASSWORD')
# DEFAULT_FROM_EMAIL = 'noreply@tudominio.com'


# ==================== LÍMITES DE UPLOAD ====================

# Tamaño máximo de archivo en memoria: 5MB
FILE_UPLOAD_MAX_MEMORY_SIZE = 5242880  # 5MB en bytes

# Tamaño máximo de request: 5MB
DATA_UPLOAD_MAX_MEMORY_SIZE = 5242880


# ==================== CACHÉ ====================

# Caché en memoria local (desarrollo)
# Para producción usar Redis o Memcached
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'unique-snowflake',
    }
}

# Para Redis (producción):
# CACHES = {
#     'default': {
#         'BACKEND': 'django.core.cache.backends.redis.RedisCache',
#         'LOCATION': 'redis://127.0.0.1:6379/1',
#     }
# }


# ==================== OTROS ====================

# Tipo de campo primary key por defecto
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'


# ==================== NOTAS DE CONFIGURACIÓN ====================

"""
VARIABLES DE ENTORNO QUE SE ESPERA IMPLEMENTAR:

Crear archivo .env en la raíz del proyecto:

SECRET_KEY=tu-clave-secreta-muy-larga-y-aleatoria
DEBUG=False
ALLOWED_HOSTS=tudominio.com,www.tudominio.com
DB_NAME=nombre_bd
DB_USER=usuario_bd
DB_PASSWORD=contraseña_segura
DB_HOST=localhost
DB_PORT=5432
EMAIL_USER=tu@email.com
EMAIL_PASSWORD=tu_password

Para usar .env instalar python-decouple:
pip install python-decouple

Luego en settings.py:
from decouple import config
SECRET_KEY = config('SECRET_KEY')
DEBUG = config('DEBUG', default=False, cast=bool)
"""

"""
COMANDOS ÚTILES:

1. Crear migraciones:
   python manage.py makemigrations

2. Aplicar migraciones:
   python manage.py migrate

3. Crear superusuario:
   python manage.py createsuperuser

4. Recopilar archivos estáticos:
   python manage.py collectstatic

5. Ejecutar servidor:
   python manage.py runserver

6. Shell de Django:
   python manage.py shell

7. Verificar configuración:
   python manage.py check

8. Ver configuración actual:
   python manage.py diffsettings
"""
# oneProject/settings.py