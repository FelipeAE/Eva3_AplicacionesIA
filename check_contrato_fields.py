#!/usr/bin/env python
import os
import sys
import django

# Add the parent directory to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Configure Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'chatbot_web.settings')
django.setup()

from chatbot.models import Contrato

print("=== VERIFICANDO CAMPOS DEL MODELO CONTRATO ===")
# Get a sample contract
contrato = Contrato.objects.first()
if contrato:
    print(f"Contrato ID: {contrato.id_contrato}")
    print("Campos disponibles:")
    for field in contrato._meta.fields:
        field_name = field.name
        try:
            field_value = getattr(contrato, field_name)
            print(f"  {field_name}: {type(field_value)} = {field_value}")
        except Exception as e:
            print(f"  {field_name}: Error accessing - {e}")
    
    print("\nRelaciones:")
    print(f"  persona: {hasattr(contrato, 'persona')} - {type(getattr(contrato, 'persona', None))}")
    if hasattr(contrato, 'persona') and contrato.persona:
        try:
            print(f"    nombre_completo: {contrato.persona.nombre_completo}")
        except Exception as e:
            print(f"    Error accessing persona.nombre_completo: {e}")
    
    print(f"  funcion: {hasattr(contrato, 'funcion')} - {type(getattr(contrato, 'funcion', None))}")
    if hasattr(contrato, 'funcion') and contrato.funcion:
        try:
            print(f"    descripcion_funcion: {contrato.funcion.descripcion_funcion}")
        except Exception as e:
            print(f"    Error accessing funcion.descripcion_funcion: {e}")
    
    print(f"  tiempo: {hasattr(contrato, 'tiempo')} - {type(getattr(contrato, 'tiempo', None))}")
    if hasattr(contrato, 'tiempo') and contrato.tiempo:
        try:
            print(f"    mes: {contrato.tiempo.mes}, anho: {contrato.tiempo.anho}")
        except Exception as e:
            print(f"    Error accessing tiempo fields: {e}")
else:
    print("No se encontraron contratos en la base de datos")