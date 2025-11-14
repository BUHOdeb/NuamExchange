# App/urls.py
from django.urls import path
from . import views

urlpatterns = [
    # ==================== AUTENTICACIÓN ====================
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('register/', views.register_view, name='register'),
    # ==================== HOME ====================
    path('', views.home, name='home'),

    # ==================== CRUD DE USUARIOS ====================
    path('usuarios/', views.listar_usuarios, name='listar_usuarios'),
    path('crear/', views.crear_usuario, name='crear_usuario'),
    path('eliminar-multiple/', views.eliminar_multiples_usuarios, name='eliminar_multiples'),
    path('editar/<int:usuario_id>/', views.editar_usuario, name='editar_usuario'),


    # ==================== IMPORTACIÓN DE EXCEL ====================
    path('upload-excel/', views.UploadExcelView.as_view(), name='upload_excel'),
    path('plantilla/', views.descargar_plantilla, name='descargar_plantilla'),
]