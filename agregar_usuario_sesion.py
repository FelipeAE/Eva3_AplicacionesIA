#!/usr/bin/env python
"""
Script para agregar la columna usuario_id a la tabla sesion_chat
"""
import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'chatbot_web.settings')
django.setup()

from django.db import connection

def agregar_columna_usuario():
    """Agrega la columna usuario_id a la tabla sesion_chat"""
    
    with connection.cursor() as cursor:
        try:
            print("🔄 Agregando columna usuario_id...")
            # Agregar la columna
            cursor.execute("ALTER TABLE sesion_chat ADD COLUMN usuario_id INTEGER;")
            print("✅ Columna usuario_id agregada")
            
            print("🔄 Creando foreign key constraint...")
            # Crear foreign key
            cursor.execute("""
                ALTER TABLE sesion_chat 
                ADD CONSTRAINT fk_sesion_chat_usuario 
                FOREIGN KEY (usuario_id) REFERENCES auth_user(id) ON DELETE CASCADE;
            """)
            print("✅ Foreign key constraint creada")
            
            print("🔄 Creando índice...")
            # Crear índice
            cursor.execute("CREATE INDEX idx_sesion_chat_usuario_id ON sesion_chat(usuario_id);")
            print("✅ Índice creado")
            
            print("🔄 Verificando estructura de la tabla...")
            # Verificar que se agregó la columna
            cursor.execute("""
                SELECT column_name, data_type, is_nullable 
                FROM information_schema.columns 
                WHERE table_name = 'sesion_chat' 
                ORDER BY ordinal_position;
            """)
            
            columns = cursor.fetchall()
            print("\n📋 Estructura actual de la tabla sesion_chat:")
            for col in columns:
                print(f"  - {col[0]}: {col[1]} (nullable: {col[2]})")
            
        except Exception as e:
            print(f"❌ Error: {e}")
            print("💡 La columna puede que ya exista o hay otro problema")

if __name__ == "__main__":
    agregar_columna_usuario()
