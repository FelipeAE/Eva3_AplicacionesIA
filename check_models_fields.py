#!/usr/bin/env python
import os
import sys
import django

# Add the parent directory to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Configure Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'chatbot_web.settings')
django.setup()

from chatbot.models import ContextoPrompt, TerminoExcluido

print("=== VERIFICANDO CAMPOS DEL MODELO ContextoPrompt ===")
if ContextoPrompt.objects.exists():
    context = ContextoPrompt.objects.first()
    print(f"Contexto ID: {context.id}")
    print("Campos disponibles:")
    for field in context._meta.fields:
        field_name = field.name
        try:
            field_value = getattr(context, field_name)
            print(f"  {field_name}: {type(field_value)} = {field_value}")
        except Exception as e:
            print(f"  {field_name}: Error accessing - {e}")
else:
    print("No hay contextos en la base de datos")

print("\n=== VERIFICANDO CAMPOS DEL MODELO TerminoExcluido ===")
if TerminoExcluido.objects.exists():
    term = TerminoExcluido.objects.first()
    print(f"Término ID: {term.id}")
    print("Campos disponibles:")
    for field in term._meta.fields:
        field_name = field.name
        try:
            field_value = getattr(term, field_name)
            print(f"  {field_name}: {type(field_value)} = {field_value}")
        except Exception as e:
            print(f"  {field_name}: Error accessing - {e}")
else:
    print("No hay términos excluidos en la base de datos")