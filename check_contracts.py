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

print("=== VERIFICANDO CONTRATOS EN LA BASE DE DATOS ===")
contratos = Contrato.objects.all()[:5]  # Solo primeros 5
print(f"Total de contratos: {Contrato.objects.count()}")
print("Primeros 5 contratos:")

for c in contratos:
    print(f"ID: {c.id_contrato}")
    if hasattr(c, 'persona') and c.persona:
        print(f"  Persona: {c.persona.nombre_completo if hasattr(c.persona, 'nombre_completo') else 'N/A'}")
    if hasattr(c, 'honorario_total_bruto') and c.honorario_total_bruto:
        print(f"  Honorario: {c.honorario_total_bruto}")
    print()