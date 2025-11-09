from django.shortcuts import render
from .models import Usuario
import pandas as pd

# Create your views here.
def home(request):
    
    return render(request, 'home.html')

def listar_usuarios(request):
    context = {}
    
    usuarios = Usuario.objects.all()

    context = {'usuarios':usuarios}

    return render(request, 'listar.html', context)

