#!/usr/bin/env python
"""
Script para asignar las sesiones existentes al superusuario
"""
import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'chatbot_web.settings')
django.setup()

from django.db import connection
from django.contrib.auth.models import User

def asignar_sesiones_a_superuser():
    """Asigna todas las sesiones sin usuario al primer superusuario"""
    
    # Buscar el primer superusuario
    superuser = User.objects.filter(is_superuser=True).first()
    
    if not superuser:
        print("❌ No se encontró ningún superusuario")
        return
    
    print(f"📋 Asignando sesiones al superusuario: {superuser.username}")
    
    with connection.cursor() as cursor:
        # Contar sesiones sin usuario
        cursor.execute("SELECT COUNT(*) FROM sesion_chat WHERE usuario_id IS NULL;")
        count_sin_usuario = cursor.fetchone()[0]
        
        print(f"🔍 Sesiones sin usuario encontradas: {count_sin_usuario}")
        
        if count_sin_usuario > 0:
            # Asignar todas las sesiones sin usuario al superusuario
            cursor.execute(
                "UPDATE sesion_chat SET usuario_id = %s WHERE usuario_id IS NULL;",
                [superuser.id]
            )
            
            print(f"✅ {count_sin_usuario} sesiones asignadas al usuario {superuser.username}")
        else:
            print("ℹ️ No hay sesiones sin usuario para asignar")
            
        # Verificar el resultado
        cursor.execute("SELECT COUNT(*) FROM sesion_chat WHERE usuario_id IS NULL;")
        count_restante = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM sesion_chat WHERE usuario_id = %s;", [superuser.id])
        count_superuser = cursor.fetchone()[0]
        
        print(f"\n📊 Estado final:")
        print(f"  - Sesiones sin usuario: {count_restante}")
        print(f"  - Sesiones del superusuario: {count_superuser}")

if __name__ == "__main__":
    asignar_sesiones_a_superuser()
