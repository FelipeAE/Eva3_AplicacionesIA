#!/usr/bin/env python
"""
Script de prueba para demostrar cómo funcionan los términos excluidos
"""
import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'chatbot_web.settings')
django.setup()

from chatbot.bot import obtener_consulta_sql

def test_exclusions():
    """Prueba la función con términos excluidos"""
    
    print("=== PRUEBA DE TÉRMINOS EXCLUIDOS ===\n")
    
    # Caso 1: Sin términos excluidos
    print("1. SIN términos excluidos:")
    print("Pregunta: 'Dame el top 5 de honorarios'")
    query1 = obtener_consulta_sql(
        "Dame el top 5 de honorarios", 
        [], 
        terminos_excluidos=None
    )
    print(f"SQL generado:\n{query1}\n")
    
    # Caso 2: Con términos excluidos
    print("2. CON términos excluidos ['marzo', 'psicólogo']:")
    print("Pregunta: 'Dame el top 5 de honorarios'")
    query2 = obtener_consulta_sql(
        "Dame el top 5 de honorarios", 
        [], 
        terminos_excluidos=['marzo', 'psicólogo']
    )
    print(f"SQL generado:\n{query2}\n")
    
    # Caso 3: Términos excluidos con región
    print("3. CON términos excluidos ['valparaíso', 'santiago']:")
    print("Pregunta: 'Muestra los contratos por región'")
    query3 = obtener_consulta_sql(
        "Muestra los contratos por región", 
        [], 
        terminos_excluidos=['valparaíso', 'santiago']
    )
    print(f"SQL generado:\n{query3}\n")
    
    print("=== PRUEBA COMPLETADA ===")

if __name__ == "__main__":
    test_exclusions()
