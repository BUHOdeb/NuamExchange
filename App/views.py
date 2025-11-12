# App/views.py
from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse, HttpResponse
from django.views import View
from .models import Usuario, ImportAudit, UsuarioHistorico
import pandas as pd
import io
from datetime import datetime
from django.contrib import messages

def home(request):
    # Obtener estadísticas para la home
    total_usuarios = Usuario.objects.count()
    recent_imports = ImportAudit.objects.all()[:5]
    usuarios_recientes = Usuario.objects.all()[:10]
    
    context = {
        'total_usuarios': total_usuarios,
        'recent_imports': recent_imports,
        'usuarios_recientes': usuarios_recientes,
    }
    
    return render(request, 'home.html', context)

def nuam(request):

    return render(request,'nuam.html')



def listar_usuarios(request):
    usuarios = Usuario.objects.all()
    context = {'usuarios': usuarios}
    return render(request, 'listar.html', context)





def crear_usuario(request):
    if request.method == 'POST':
        nombre = request.POST.get('first_name')
        apellido = request.POST.get('last_name')
        edad = request.POST.get('edad')
        email = request.POST.get('email')
        telefono = request.POST.get('telefono')

        Usuario.objects.create(
            first_name=nombre,
            last_name=apellido,
            edad=edad,
            email=email,
            telefono=telefono
        )

    return render(request, 'crear.html')


class UploadExcelView(View):
    def post(self, request):
        try:
            file = request.FILES.get('file')
            
            if not file:
                return JsonResponse({
                    'status': 'error',
                    'message': 'No se ha seleccionado ningún archivo'
                }, status=400)
            
            # Verificar extensión
            file_name = file.name.lower()
            if not (file_name.endswith('.xlsx') or file_name.endswith('.xls') or file_name.endswith('.csv')):
                return JsonResponse({
                    'status': 'error',
                    'message': 'Formato de archivo no válido. Use .xlsx, .xls o .csv'
                }, status=400)
            
            # Crear registro de auditoría
            audit = ImportAudit.objects.create(
                user=request.user if request.user.is_authenticated else None,
                filename=file.name,
                status=ImportAudit.STATUS_PENDING
            )
            
            # Leer el archivo
            try:
                file.seek(0)
                if file_name.endswith('.csv'):
                    df = pd.read_csv(file, encoding='utf-8')
                else:
                    df = pd.read_excel(file)
            except Exception as e:
                audit.status = ImportAudit.STATUS_FAILED
                audit.errors = [{'error': f'Error al leer archivo: {str(e)}'}]
                audit.save()
                return JsonResponse({
                    'status': 'error',
                    'message': f'Error al leer el archivo: {str(e)}'
                }, status=400)
            
            # Validar columnas requeridas
            columnas_requeridas = ['first_name', 'last_name', 'email']
            columnas_faltantes = [col for col in columnas_requeridas if col not in df.columns]
            
            if columnas_faltantes:
                audit.status = ImportAudit.STATUS_FAILED
                audit.errors = [{'error': f'Columnas faltantes: {", ".join(columnas_faltantes)}'}]
                audit.save()
                return JsonResponse({
                    'status': 'error',
                    'message': f'Columnas faltantes: {", ".join(columnas_faltantes)}. Columnas encontradas: {", ".join(df.columns)}'
                }, status=400)
            
            # Actualizar estado
            audit.status = ImportAudit.STATUS_VALIDATED
            audit.row_count = len(df)
            audit.save()
            
            # Procesar datos
            audit.status = ImportAudit.STATUS_IMPORTING
            audit.save()
            
            usuarios_creados = 0
            usuarios_actualizados = 0
            errores = []
            
            for index, row in df.iterrows():
                row_errors = []
                
                try:
                    # Limpiar datos
                    first_name = str(row.get('first_name', '')).strip() if pd.notna(row.get('first_name')) else ''
                    last_name = str(row.get('last_name', '')).strip() if pd.notna(row.get('last_name')) else ''
                    email = str(row.get('email', '')).strip().lower() if pd.notna(row.get('email')) else ''
                    
                    if not first_name or not last_name or not email:
                        errores.append({
                            'row': index + 2,
                            'errors': ['Nombre, apellido o email vacío']
                        })
                        continue
                    
                    if '@' not in email:
                        errores.append({
                            'row': index + 2,
                            'errors': ['Email inválido']
                        })
                        continue
                    
                    # Edad
                    edad = None
                    if pd.notna(row.get('edad')) and str(row.get('edad')).strip():
                        try:
                            edad = int(float(row.get('edad')))
                            if edad < 0 or edad > 150:
                                row_errors.append('Edad inválida')
                        except:
                            row_errors.append('Edad debe ser número')
                    
                    # Teléfono
                    telefono = None
                    if pd.notna(row.get('telefono')) and str(row.get('telefono')).strip():
                        telefono = str(row.get('telefono')).strip()
                        if telefono.lower() == 'nan':
                            telefono = None
                    
                    # Fecha nacimiento
                    fecha_nacimiento = None
                    if pd.notna(row.get('fecha_nacimiento')) and str(row.get('fecha_nacimiento')).strip():
                        try:
                            fecha_str = str(row.get('fecha_nacimiento')).strip()
                            if fecha_str.lower() != 'nan':
                                for fmt in ['%Y-%m-%d', '%d/%m/%Y', '%d-%m-%Y', '%Y/%m/%d']:
                                    try:
                                        fecha_nacimiento = datetime.strptime(fecha_str, fmt).date()
                                        break
                                    except:
                                        continue
                                if not fecha_nacimiento:
                                    try:
                                        fecha_nacimiento = pd.to_datetime(row.get('fecha_nacimiento')).date()
                                    except:
                                        row_errors.append('Formato de fecha inválido')
                        except:
                            row_errors.append('Error en fecha')
                    
                    if row_errors:
                        errores.append({'row': index + 2, 'errors': row_errors})
                        continue
                    
                    # Verificar teléfono duplicado
                    if telefono:
                        if Usuario.objects.filter(telefono=telefono).exclude(email=email).exists():
                            errores.append({
                                'row': index + 2,
                                'errors': ['Teléfono duplicado']
                            })
                            continue
                    
                    # Crear o actualizar
                    usuario_existente = Usuario.objects.filter(email=email).first()
                    
                    if usuario_existente:
                        # Guardar histórico
                        UsuarioHistorico.objects.create(
                            usuario=usuario_existente,
                            first_name=usuario_existente.first_name,
                            last_name=usuario_existente.last_name,
                            edad=usuario_existente.edad,
                            email=usuario_existente.email,
                            telefono=usuario_existente.telefono,
                            fecha_nacimiento=usuario_existente.fecha_nacimiento
                        )
                        
                        # Actualizar
                        usuario_existente.first_name = first_name
                        usuario_existente.last_name = last_name
                        usuario_existente.edad = edad
                        usuario_existente.telefono = telefono
                        usuario_existente.fecha_nacimiento = fecha_nacimiento
                        usuario_existente.save()
                        usuarios_actualizados += 1
                    else:
                        # Crear
                        Usuario.objects.create(
                            first_name=first_name,
                            last_name=last_name,
                            edad=edad,
                            email=email,
                            telefono=telefono,
                            fecha_nacimiento=fecha_nacimiento
                        )
                        usuarios_creados += 1
                        
                except Exception as e:
                    errores.append({
                        'row': index + 2,
                        'errors': [f'Error: {str(e)}']
                    })
            
            # Actualizar auditoría
            audit.imported_count = usuarios_creados
            audit.updated_count = usuarios_actualizados
            audit.error_count = len(errores)
            audit.errors = errores
            audit.status = ImportAudit.STATUS_IMPORTED if usuarios_creados + usuarios_actualizados > 0 else ImportAudit.STATUS_FAILED
            audit.save()
            
            return JsonResponse({
                'status': 'success',
                'message': 'Archivo procesado exitosamente',
                'data': {
                    'creados': usuarios_creados,
                    'actualizados': usuarios_actualizados,
                    'errores': errores[:10],
                    'total_errores': len(errores),
                    'total': usuarios_creados + usuarios_actualizados,
                }
            })
            
        except Exception as e:
            return JsonResponse({
                'status': 'error',
                'message': f'Error: {str(e)}'
            }, status=500)


def descargar_plantilla(request):
    # Crear DataFrame con ejemplo
    data = {
        'first_name': ['Juan', 'María', 'Pedro'],
        'last_name': ['Pérez', 'García', 'López'],
        'edad': [25, 30, 28],
        'email': ['juan.perez@ejemplo.com', 'maria.garcia@ejemplo.com', 'pedro.lopez@ejemplo.com'],
        'telefono': ['+56912345678', '+56987654321', '+56955556666'],
        'fecha_nacimiento': ['1998-05-15', '1993-08-22', '1995-12-10']
    }
    df = pd.DataFrame(data)
    
    response = HttpResponse(
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = 'attachment; filename=plantilla_usuarios.xlsx'
    
    with pd.ExcelWriter(response, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Usuarios')
        worksheet = writer.sheets['Usuarios']
        
        for column in worksheet.columns:
            max_length = 0
            column_letter = column[0].column_letter
            for cell in column:
                try:
                    if len(str(cell.value)) > max_length:
                        max_length = len(cell.value)
                except:
                    pass
            adjusted_width = min(max_length + 2, 50)
            worksheet.column_dimensions[column_letter].width = adjusted_width
    
    return response

