# App/views.py
"""
Vistas del sistema NuamExchange
Maneja todas las peticiones HTTP y lógica de negocio
"""
from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse, HttpResponse
from django.views import View
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q
from django.utils.decorators import method_decorator
from django.core.exceptions import ValidationError
from .models import Usuario, ImportAudit
from .decorators import admin_required
from .forms import UsuarioForm
import pandas as pd
from datetime import datetime
import logging

#logger para registrar y eventos importantes
logger = logging.getLogger(__name__)

# Al inicio de App/views.py, después de los imports existentes

# ==================== AUTENTICACIÓN ====================
def register_view(request):
    """
    Vista de registro de nuevos usuarios
    
    - GET: Muestra el formulario de registro
    - POST: Crea el nuevo usuario y su perfil
    """
    
    # Si ya está autenticado, redirigir al home
    if request.user.is_authenticated:
        return redirect('home')
    
    if request.method == 'POST':
        # Obtener datos del formulario
        username = request.POST.get('username', '').strip()
        email = request.POST.get('email', '').strip().lower()
        first_name = request.POST.get('first_name', '').strip()
        last_name = request.POST.get('last_name', '').strip()
        password = request.POST.get('password')
        password2 = request.POST.get('password2')
        
        # ===== VALIDACIONES =====
        
        # 1. Validar campos obligatorios
        if not all([username, email, first_name, last_name, password, password2]):
            messages.error(request, 'Todos los campos son obligatorios')
            return render(request, 'register.html')
        
        # 2. Validar que las contraseñas coincidan
        if password != password2:
            messages.error(request, 'Las contraseñas no coinciden')
            return render(request, 'register.html')
        
        # 3. Validar longitud de contraseña
        if len(password) < 6:
            messages.error(request, 'La contraseña debe tener al menos 6 caracteres')
            return render(request, 'register.html')
        
        # 4. Validar username único
        if User.objects.filter(username=username).exists():
            messages.error(request, f'El nombre de usuario "{username}" ya está registrado')
            return render(request, 'register.html')
        
        # 5. Validar email único
        if User.objects.filter(email=email).exists():
            messages.error(request, f'El email "{email}" ya está registrado')
            return render(request, 'register.html')
        
        # 6. Validar formato de email
        if '@' not in email or '.' not in email.split('@')[1]:
            messages.error(request, 'Formato de email inválido')
            return render(request, 'register.html')
        
        try:
            # ===== CREAR USUARIO =====
            
            user = User.objects.create_user(
                username=username,
                email=email,
                first_name=first_name,
                last_name=last_name,
                password=password
            )
            
            # El perfil se crea automáticamente por la señal
            # Pero podemos asignar un rol por defecto
            user.profile.role = 'Employee'
            user.profile.save()
            
            # Registrar en logs
            logger.info(f'Nuevo usuario registrado: {username} ({email})')
            
            # Mensaje de éxito
            messages.success(
                request,
                f'¡Registro exitoso! Ya puedes iniciar sesión con tu cuenta.'
            )
            
            return redirect('login')
            
        except Exception as e:
            logger.error(f'Error en registro: {e}')
            messages.error(request, 'Error al crear la cuenta. Intente nuevamente.')
            return render(request, 'register.html')
    
    # GET request: mostrar formulario vacío
    return render(request, 'register.html')

def login_view(request):
    """
    Vista de inicio de sesión
    
    - GET: Muestra el formulario de login
    - POST: Procesa las credenciales y autentica al usuario
    """
    
    # Si ya está autenticado, redirigir al home
    if request.user.is_authenticated:
        return redirect('home')
    
    if request.method == 'POST':
        # Obtener datos del formulario
        email = request.POST.get('email', '').strip().lower()
        password = request.POST.get('password')
        
        # Validar que no estén vacíos
        if not email or not password:
            messages.error(request, 'Email y contraseña son requeridos')
            return render(request, 'login.html')
        
        try:
            # Buscar usuario por email
            user_obj = User.objects.get(email=email)
            
            # Autenticar con username y password
            user = authenticate(
                request,
                username=user_obj.username,
                password=password
            )
            
            if user is not None:
                # Autenticación exitosa
                login(request, user)
                
                # Registrar login en logs
                logger.info(f'Usuario {user.username} inició sesión')
                
                messages.success(request, f'¡Bienvenido {user.first_name}!')
                return redirect('home')
            else:
                # Contraseña incorrecta
                messages.error(request, 'Contraseña incorrecta')
                logger.warning(f'Intento de login fallido para email: {email}')
        
        except User.DoesNotExist:
            # Usuario no existe
            messages.error(request, 'No existe un usuario con ese email')
            logger.warning(f'Intento de login con email inexistente: {email}')
        
        except Exception as e:
            # Error inesperado
            logger.error(f'Error en login: {e}')
            messages.error(request, 'Error al iniciar sesión. Intente nuevamente.')
    
    return render(request, 'login.html')


def logout_view(request):
    """
    Cerrar sesión del usuario
    """
    if request.user.is_authenticated:
        username = request.user.username
        logout(request)
        logger.info(f'Usuario {username} cerró sesión')
        messages.success(request, 'Has cerrado sesión exitosamente')
    
    return redirect('login')


@login_required
def home(request):
    """
    Vista principal del sistema (Home/Dashboard)
    Muestra estadísticas generales y datos recientes
    
    Requiere autenticación (@login_required)
    """
    # Obtener estadísticas
    total_usuarios = Usuario.objects.filter(is_active=True).count()
    
    # Usuarios creados hoy
    usuarios_hoy = Usuario.objects.filter(
        created_at__date=datetime.now().date()
    ).count()
    
    # Últimas 5 importaciones del usuario actual
    recent_imports = ImportAudit.objects.filter(
        user=request.user
    ).order_by('-uploaded_at')[:5]
    
    # Últimos 10 usuarios creados
    usuarios_recientes = Usuario.objects.filter(
        is_active=True
    ).order_by('-created_at')[:10]
    
    # Obtener rol del usuario
    user_role = 'Employee'  # Por defecto
    if hasattr(request.user, 'profile'):
        user_role = request.user.profile.role
    
    # Preparar contexto para el template
    context = {
        'total_usuarios': total_usuarios,
        'usuarios_hoy': usuarios_hoy,
        'recent_imports': recent_imports,
        'usuarios_recientes': usuarios_recientes,
        'user_role': user_role
    }
    
    return render(request, 'home.html', context)

@login_required
def eliminar_multiples_usuarios(request):
    if request.method == "POST":
        ids = request.POST.getlist("usuarios")  # lista de IDs seleccionados
        if not ids:
            messages.error(request, "No seleccionaste ningún usuario para eliminar.")
            return redirect("listar_usuarios")

        User.objects.filter(id__in=ids).delete()
        messages.success(request, f"Se eliminaron {len(ids)} usuarios correctamente.")
        return redirect("listar_usuarios")

    # GET → mostrar tabla de usuarios con casillas para seleccionar
    usuarios = User.objects.all().order_by("id")
    return render(request, "eliminar_multiples.html", {"usuarios": usuarios})

@login_required
def listar_usuarios(request):
    """
    Listar todos los usuarios con funcionalidades de:
    - Búsqueda por nombre, apellido, email o teléfono
    - Ordenamiento por diferentes campos
    - Paginación (20 registros por página)
    
    Parámetros GET:
    - q: término de búsqueda
    - order_by: campo para ordenar
    - page: número de página
    """
    
    # Obtener parámetro de búsqueda
    query = request.GET.get('q', '').strip()
    
    # Consulta base: solo usuarios activos
    usuarios_list = Usuario.objects.filter(is_active=True)
    
    # Aplicar búsqueda si existe término
    if query:
        usuarios_list = usuarios_list.filter(
            Q(first_name__icontains=query) |      # Buscar en nombre
            Q(last_name__icontains=query) |       # Buscar en apellido
            Q(email__icontains=query) |           # Buscar en email
            Q(telefono__icontains=query)          # Buscar en teléfono
        )
        
        logger.info(f'Búsqueda realizada por {request.user.username}: "{query}"')
    
    # Aplicar ordenamiento
    order_by = request.GET.get('order_by', '-created_at')
    
    # Lista blanca de campos permitidos para ordenar
    allowed_ordering = [
        'first_name', '-first_name',
        'last_name', '-last_name',
        'email', '-email',
        'edad', '-edad',
        'created_at', '-created_at'
    ]
    
    if order_by in allowed_ordering:
        usuarios_list = usuarios_list.order_by(order_by)
    else:
        # Si el campo no es válido, usar ordenamiento por defecto
        usuarios_list = usuarios_list.order_by('-created_at')
    
    # Implementar paginación
    paginator = Paginator(usuarios_list, 20)  # 20 usuarios por página
    page_number = request.GET.get('page', 1)
    
    try:
        usuarios = paginator.get_page(page_number)
    except:
        usuarios = paginator.get_page(1)
    
    # Preparar contexto
    context = {
        'usuarios': usuarios,
        'query': query,
        'order_by': order_by,
        'total': usuarios_list.count()
    }
    
    return render(request, 'listar.html', context)


@login_required
def crear_usuario(request):
    """
    Crear un nuevo usuario en el sistema
    
    - GET: Muestra el formulario vacío
    - POST: Procesa y crea el usuario con validaciones
    
    Validaciones:
    - Campos obligatorios: nombre, apellido, email
    - Email único
    - Contraseña de minimo 6 caracteres (Obligatoria)
    - Teléfono único (si se proporciona)
    - Edad entre 0-150
    - Fecha de nacimiento no futura
    """
    
    if request.method == 'POST':
        try:
            # Obtener datos del formulario y limpiarlos
            first_name = request.POST.get('first_name', '').strip()
            last_name = request.POST.get('last_name', '').strip()
            email = request.POST.get('email', '').strip().lower()
            password = request.POST.get('password', '')
            edad = request.POST.get('edad', '').strip()
            telefono = request.POST.get('telefono', '').strip()
            fecha_nacimiento = request.POST.get('fecha_nacimiento', '').strip()
            
            # ===== VALIDACIONES =====
            
            # 1. Validar campos obligatorios
            if not all([first_name, last_name, email, password]):
                messages.error(request, 'Nombre, apellido y email son obligatorios')
                return render(request, 'crear.html')
            
            # 2. Validar email único
            if Usuario.objects.filter(email=email).exists():
                messages.error(request, f'El email {email} ya está registrado')
                return render(request, 'crear.html')
            
            # 3. Validar teléfono único (si se proporciona)
            if telefono and Usuario.objects.filter(telefono=telefono).exists():
                messages.error(request, f'El teléfono {telefono} ya está registrado')
                return render(request, 'crear.html')
            
            # 4. Convertir y validar edad
            edad_int = None
            if edad:
                try:
                    edad_int = int(edad)
                    if edad_int < 0 or edad_int > 150:
                        messages.error(request, 'La edad debe estar entre 0 y 150')
                        return render(request, 'crear.html')
                except ValueError:
                    messages.error(request, 'Edad inválida')
                    return render(request, 'crear.html')
            
            # 5. Convertir y validar fecha de nacimiento
            fecha_obj = None
            if fecha_nacimiento:
                try:
                    fecha_obj = datetime.strptime(fecha_nacimiento, '%Y-%m-%d').date()
                    
                    # No puede ser fecha futura
                    if fecha_obj > datetime.now().date():
                        messages.error(request, 'La fecha de nacimiento no puede ser futura')
                        return render(request, 'crear.html')
                except ValueError:
                    messages.error(request, 'Formato de fecha inválido. Use YYYY-MM-DD')
                    return render(request, 'crear.html')
                
            # 6. Validar contraseña
            if not password or len(password) < 6:
                messages.error(request, 'La contraseña es obligatoria y debe tener mas de 6 caracteres :D.')

                return render(request, 'home.html')
            
            # ===== CREAR USUARIO =====
            
            usuario = Usuario.objects.create(
                first_name=first_name,
                last_name=last_name,
                email=email,
                edad=edad_int,
                telefono=telefono if telefono else None,
                fecha_nacimiento=fecha_obj,
                created_by=request.user  # Registrar quién creó el usuario
            )
            
            # Registrar en logs
            logger.info(
                f'Usuario {usuario.email} creado por {request.user.username}'
            )
            
            # Mensaje de éxito
            messages.success(
                request,
                f'Usuario {first_name} {last_name} creado exitosamente'
            )
            
            return redirect('listar_usuarios')
            
        except ValidationError as e:
            # Errores de validación del modelo
            messages.error(request, f'Error de validación: {e}')
            logger.warning(f'Error de validación al crear usuario: {e}')
        
        except Exception as e:
            # Cualquier otro error
            logger.error(f'Error inesperado creando usuario: {e}')
            messages.error(request, 'Error al crear usuario. Intente nuevamente.')

        usuario.set_password(password)
        usuario.save()
    
    # GET request: mostrar formulario vacío
    return render(request, 'crear.html')

@login_required
# @admin_required  # Solo administradores pueden eliminar
def eliminar_multiples_usuarios(request):
    """
    Vista para eliminación múltiple de usuarios con:
    - Búsqueda
    - Ordenamiento
    - Paginación
    - Eliminación masiva por checkboxes
    """

    # Obtener término de búsqueda
    query = request.GET.get('q', '').strip()

    # Base: solo usuarios activos
    usuarios_list = Usuario.objects.filter(is_active=True)

    # Aplicar búsqueda
    if query:
        usuarios_list = usuarios_list.filter(
            Q(first_name__icontains=query) |
            Q(last_name__icontains=query) |
            Q(email__icontains=query) |
            Q(telefono__icontains=query)
        )

    # Ordenamiento
    order_by = request.GET.get('order_by', '-created_at')

    allowed_ordering = [
        'first_name', '-first_name',
        'last_name', '-last_name',
        'email', '-email',
        'edad', '-edad',
        'created_at', '-created_at',
    ]

    if order_by in allowed_ordering:
        usuarios_list = usuarios_list.order_by(order_by)
    else:
        usuarios_list = usuarios_list.order_by('-created_at')

    # Paginación
    paginator = Paginator(usuarios_list, 20)
    page_number = request.GET.get('page', 1)

    try:
        usuarios = paginator.get_page(page_number)
    except:
        usuarios = paginator.get_page(1)

    # ============================
    # PROCESAR ELIMINACIÓN (POST)
    # ============================
    if request.method == "POST":
        ids = request.POST.getlist("usuarios")

        if ids:
            eliminados = Usuario.objects.filter(id__in=ids).delete()
            messages.success(
                request,
                f"Se eliminaron {len(ids)} usuarios correctamente."
            )
        else:
            messages.warning(request, "No seleccionaste ningún usuario.")

        return redirect("eliminar_multiples")

    # Contexto
    context = {
        "usuarios": usuarios,
        "query": query,
        "order_by": order_by,
        "total": usuarios_list.count(),
    }

    return render(request, "deletemulti.html", context)

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.models import User
from .models import Usuario  # si tienes un modelo extendido

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.models import User
from .models import Usuario  # si tienes un modelo extendido

def editar_usuario(request, usuario_id):
    usuario = get_object_or_404(Usuario, id=usuario_id)  # Ajusta el modelo según el tuyo

    if request.method == "POST":
        # Obtener datos del formulario
        usuario.first_name = request.POST.get("nombre")
        usuario.last_name = request.POST.get("apellido")
        usuario.email = request.POST.get("email")
        usuario.edad = request.POST.get("edad") or None
        usuario.telefono = request.POST.get("telefono") or None
        usuario.fecha_nacimiento = request.POST.get("fecha_nacimiento") or None

        usuario.save()

        messages.success(request, "Usuario actualizado correctamente.")
        return redirect("listar_usuarios")

    # Si es GET → mostrar formulario
    return render(request, "editar.html", {"usuario": usuario})


# ==================== IMPORTACIÓN EXCEL ====================

@method_decorator(login_required, name='dispatch')
class UploadExcelView(View):
    """
    Vista basada en clase para importación de archivos Excel
    
    Procesa archivos .xlsx, .xls o .csv con usuarios
    Incluye validaciones robustas y auditoría completa
    
    Límites:
    - Tamaño máximo: 5MB
    - Registros máximos: 1000
    
    Columnas requeridas:
    - first_name
    - last_name
    - email
    
    Columnas opcionales:
    - edad
    - telefono
    - fecha_nacimiento
    """
    
    def post(self, request):
        """
        Procesar archivo Excel/CSV
        
        Returns:
            JsonResponse con resultado de la importación
        """
        
        # Registrar tiempo de inicio
        start_time = datetime.now()
        
        try:
            # ===== VALIDACIONES INICIALES =====
            
            file = request.FILES.get('file')
            
            if not file:
                return JsonResponse({
                    'status': 'error',
                    'message': 'No se seleccionó archivo'
                }, status=400)
            
            # 1. Validar tamaño (máximo 5MB)
            max_size = 5 * 1024 * 1024  # 5MB en bytes
            if file.size > max_size:
                return JsonResponse({
                    'status': 'error',
                    'message': f'El archivo es muy grande. Máximo {max_size/(1024*1024):.0f}MB'
                }, status=400)
            
            # 2. Validar extensión
            file_name = file.name.lower()
            valid_extensions = ['.xlsx', '.xls', '.csv']
            
            if not any(file_name.endswith(ext) for ext in valid_extensions):
                return JsonResponse({
                    'status': 'error',
                    'message': f'Formato inválido. Use: {", ".join(valid_extensions)}'
                }, status=400)
            
            # ===== CREAR AUDITORÍA =====
            
            audit = ImportAudit.objects.create(
                user=request.user,
                filename=file.name,
                status=ImportAudit.STATUS_PENDING
            )
            
            logger.info(f'Iniciando importación {audit.id} por {request.user.username}')
            
            # ===== LEER ARCHIVO =====
            
            try:
                file.seek(0)  # Volver al inicio del archivo
                
                if file_name.endswith('.csv'):
                    # Leer CSV con encoding UTF-8
                    df = pd.read_csv(file, encoding='utf-8')
                else:
                    # Leer Excel
                    df = pd.read_excel(file)
                
                logger.info(f'Archivo leído: {len(df)} filas')
                
            except Exception as e:
                # Error al leer archivo
                audit.status = ImportAudit.STATUS_FAILED
                audit.errors = [{'error': f'Error leyendo archivo: {str(e)}'}]
                audit.save()
                
                logger.error(f'Error leyendo archivo en importación {audit.id}: {e}')
                
                return JsonResponse({
                    'status': 'error',
                    'message': f'Error al leer archivo: {str(e)}'
                }, status=400)
            
            # ===== VALIDAR COLUMNAS =====
            
            required_cols = ['first_name', 'last_name', 'email']
            missing = [col for col in required_cols if col not in df.columns]
            
            if missing:
                audit.status = ImportAudit.STATUS_FAILED
                audit.errors = [{'error': f'Columnas faltantes: {", ".join(missing)}'}]
                audit.save()
                
                return JsonResponse({
                    'status': 'error',
                    'message': f'Columnas faltantes: {", ".join(missing)}. '
                              f'Columnas encontradas: {", ".join(df.columns)}'
                }, status=400)
            
            # ===== VALIDAR CANTIDAD =====
            
            max_rows = 1000
            if len(df) > max_rows:
                audit.status = ImportAudit.STATUS_FAILED
                audit.errors = [{'error': f'Máximo {max_rows} filas permitidas'}]
                audit.save()
                
                return JsonResponse({
                    'status': 'error',
                    'message': f'El archivo excede el límite de {max_rows} registros'
                }, status=400)
            
            # ===== PROCESAR DATOS =====
            
            audit.status = ImportAudit.STATUS_IMPORTING
            audit.row_count = len(df)
            audit.save()
            
            logger.info(f'Procesando {len(df)} registros...')
            
            created = 0
            updated = 0
            errors = []
            
            # Iterar sobre cada fila del DataFrame
            for idx, row in df.iterrows():
                try:
                    # Limpiar datos básicos
                    first_name = str(row.get('first_name', '')).strip()
                    last_name = str(row.get('last_name', '')).strip()
                    email = str(row.get('email', '')).strip().lower()
                    
                    # Validar campos obligatorios
                    if not all([first_name, last_name, email]):
                        errors.append({
                            'row': idx + 2,  # +2 porque índice empieza en 0 y hay header
                            'errors': ['Campos obligatorios vacíos']
                        })
                        continue
                    
                    # Validar formato de email
                    if '@' not in email or '.' not in email.split('@')[1]:
                        errors.append({
                            'row': idx + 2,
                            'errors': ['Email inválido']
                        })
                        continue
                    
                    # Procesar edad (opcional)
                    edad = None
                    if pd.notna(row.get('edad')):
                        try:
                            edad = int(float(row.get('edad')))
                            if edad < 0 or edad > 150:
                                errors.append({
                                    'row': idx + 2,
                                    'errors': ['Edad debe estar entre 0 y 150']
                                })
                                continue
                        except:
                            pass
                    
                    # Procesar teléfono (opcional)
                    telefono = None
                    if pd.notna(row.get('telefono')):
                        telefono = str(row.get('telefono')).strip()
                        # Ignorar valores como 'nan', 'NaN', etc.
                        if telefono.lower() in ['nan', 'none', '']:
                            telefono = None
                    
                    # Procesar fecha de nacimiento (opcional)
                    fecha_nac = None
                    if pd.notna(row.get('fecha_nacimiento')):
                        try:
                            fecha_nac = pd.to_datetime(
                                row.get('fecha_nacimiento')
                            ).date()
                        except:
                            pass
                    
                    # Crear o actualizar usuario
                    usuario, was_created = Usuario.objects.update_or_create(
                        email=email,
                        defaults={
                            'first_name': first_name,
                            'last_name': last_name,
                            'edad': edad,
                            'telefono': telefono,
                            'fecha_nacimiento': fecha_nac,
                            'created_by': request.user,
                            'is_active': True
                        }
                    )
                    
                    if was_created:
                        created += 1
                    else:
                        updated += 1
                    
                except Exception as e:
                    # Error procesando fila específica
                    errors.append({
                        'row': idx + 2,
                        'errors': [str(e)]
                    })
                    logger.error(f'Error en fila {idx + 2}: {e}')
            
            # ===== FINALIZAR AUDITORÍA =====
            
            end_time = datetime.now()
            
            audit.imported_count = created
            audit.updated_count = updated
            audit.error_count = len(errors)
            audit.errors = errors[:20]  # Guardar solo primeros 20 errores
            audit.status = (
                ImportAudit.STATUS_IMPORTED 
                if (created + updated) > 0 
                else ImportAudit.STATUS_FAILED
            )
            audit.processing_time = end_time - start_time
            audit.save()
            
            # Registrar resultado en logs
            logger.info(
                f'Importación {audit.id} completada: '
                f'{created} creados, {updated} actualizados, {len(errors)} errores'
            )
            
            # Retornar resultado
            return JsonResponse({
                'status': 'success',
                'message': 'Importación completada',
                'data': {
                    'creados': created,
                    'actualizados': updated,
                    'errores': errors[:10],  # Solo primeros 10 para respuesta
                    'total_errores': len(errors)
                }
            })
            
        except Exception as e:
            # Error inesperado
            logger.error(f'Error crítico en importación: {e}')
            return JsonResponse({
                'status': 'error',
                'message': f'Error: {str(e)}'
            }, status=500)


@login_required
def descargar_plantilla(request):
    """
    Descargar plantilla Excel de ejemplo
    
    Genera un archivo .xlsx con:
    - Headers correctos
    - 3 filas de ejemplo
    - Formato adecuado
    
    Returns:
        HttpResponse con archivo Excel
    """
    
    # Datos de ejemplo
    data = {
        'first_name': ['Juan', 'María', 'Pedro'],
        'last_name': ['Pérez', 'García', 'López'],
        'edad': [25, 30, 28],
        'email': ['juan@ejemplo.com', 'maria@ejemplo.com', 'pedro@ejemplo.com'],
        'telefono': ['+56912345678', '+56987654321', '+56955556666'],
        'fecha_nacimiento': ['1998-05-15', '1993-08-22', '1995-12-10']
    }
    
    # Crear DataFrame
    df = pd.DataFrame(data)
    
    # Preparar respuesta HTTP
    response = HttpResponse(
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = 'attachment; filename=plantilla_usuarios.xlsx'
    
    # Escribir Excel en la respuesta
    with pd.ExcelWriter(response, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Usuarios')
    
    logger.info(f'Plantilla descargada por {request.user.username}')
    
    return response

