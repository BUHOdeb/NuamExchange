# App/admin.py

from django.contrib import admin
from .models import Usuario, ImportAudit

# Register your models here.
@admin.register(Usuario)
class UsuarioAdmin(admin.ModelAdmin):
    list_display = ('id', 'first_name', 'last_name','fecha_nacimiento')

@admin.register(ImportAudit)
class ImportAuditAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'uploaded_at', 'filename')