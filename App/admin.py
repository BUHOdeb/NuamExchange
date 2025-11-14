# App/admin.py

from django.contrib import admin
from .models import Usuario, ImportAudit, Categoria

# Register your models here.
@admin.register(Usuario)
class UsuarioAdmin(admin.ModelAdmin):
    list_display = ('id', 'first_name', 'last_name','fecha_nacimiento')

@admin.register(Categoria)
class CategoriaAdmin(admin.ModelAdmin):
    list_display = ('id','name')

@admin.register(ImportAudit)
class ImportAuditAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'uploaded_at', 'filename')
    # App/admin.py