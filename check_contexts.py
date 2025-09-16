#!/usr/bin/env python
import os
import sys
import django

# Add the parent directory to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Configure Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'chatbot_web.settings')
django.setup()

from chatbot.models import ContextoPrompt
from django.contrib.auth.models import User

print("=== VERIFICANDO CONTEXTOS EN LA BASE DE DATOS ===")
contextos = ContextoPrompt.objects.all()
print(f"Total de contextos: {contextos.count()}")

for c in contextos:
    print(f"ID: {c.id}, Nombre: {c.nombre}, Activo: {c.activo}")
    print(f"  Prompt: {c.prompt_sistema[:100]}...")
    if hasattr(c, 'fecha_creacion'):
        print(f"  Fecha: {c.fecha_creacion}")
    print()

print("=== VERIFICANDO USUARIOS SUPERUSER ===")
superusers = User.objects.filter(is_superuser=True)
print(f"Total superusers: {superusers.count()}")
for u in superusers:
    print(f"Username: {u.username}, Staff: {u.is_staff}, Superuser: {u.is_superuser}")

print("=== VERIFICANDO USUARIOS STAFF ===")
staff_users = User.objects.filter(is_staff=True)
print(f"Total staff users: {staff_users.count()}")
for u in staff_users:
    print(f"Username: {u.username}, Staff: {u.is_staff}, Superuser: {u.is_superuser}")