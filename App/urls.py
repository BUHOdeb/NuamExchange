# App/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('usuarios/', views.listar_usuarios, name='listar_usuarios'),
    path('crear/', views.crear_usuario, name='crear_usuario'),
    path('upload-excel/', views.UploadExcelView.as_view(), name='upload_excel'),
    path('descargar-plantilla/', views.descargar_plantilla, name='descargar_plantilla'),
    path('nuam/', views.nuam, name='nuam'),
    path('editar/int:pk/', views.editar_datos, name='editar_datos'),
    ]