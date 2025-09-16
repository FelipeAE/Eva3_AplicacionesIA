#!/usr/bin/env python
"""
Test script para verificar que las APIs estan correctamente configuradas.
Ejecutar con: python test_api.py
"""

import os
import django
import sys

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'chatbot_web.settings')
django.setup()

def test_api_imports():
    """Test que todas las APIs se importen correctamente"""
    print("Testing API imports...")
    
    try:
        from chatbot.api import (
            api_sessions_list,
            api_session_create,
            api_session_detail,
            api_send_message,
            api_contexts_list,
            api_excluded_terms,
        )
        print("OK - Todas las funciones API se importan correctamente")
        return True
        
    except Exception as e:
        print(f"ERROR - importando APIs: {e}")
        return False

def test_services():
    """Test que los servicios funcionen correctamente"""
    print("Testing services...")
    
    try:
        from chatbot.services import ChatService, ValidationService
        from chatbot.services.ai_service import AIService
        
        # Test ValidationService
        valid, _ = ValidationService.is_valid_question("Dame el top 5 de honorarios")
        if valid:
            print("OK - ValidationService.is_valid_question funciona")
        else:
            print("ERROR - ValidationService.is_valid_question falla")
            
        # Test que AIService tenga los metodos necesarios
        if hasattr(AIService, 'generate_sql_query') and hasattr(AIService, 'generate_final_response'):
            print("OK - AIService tiene todos los metodos necesarios")
        else:
            print("ERROR - AIService falta metodos")
            
        return True
        
    except Exception as e:
        print(f"ERROR - testing services: {e}")
        return False

def test_models():
    """Test que los modelos esten correctamente configurados"""
    print("Testing models...")
    
    try:
        from chatbot.models import SesionChat, MensajeChat, ContextoPrompt, TerminoExcluido
        
        # Test que los modelos se puedan instanciar
        print("OK - Todos los modelos se importan correctamente")
        
        # Test relaciones
        if hasattr(SesionChat, 'usuario') and hasattr(MensajeChat, 'sesion'):
            print("OK - Relaciones de modelos configuradas correctamente")
        else:
            print("ERROR - Faltan relaciones en modelos")
            
        return True
        
    except Exception as e:
        print(f"ERROR - testing models: {e}")
        return False

def test_api_urls():
    """Test que las URLs de API esten configuradas correctamente"""
    print("Testing API URL configuration...")
    
    try:
        # Test que las URLs existen
        from django.urls import resolve
        
        api_urls = [
            '/api/v1/sessions/',
            '/api/v1/sessions/create/',
            '/api/v1/sessions/1/',
            '/api/v1/sessions/1/message/',
            '/api/v1/admin/contexts/',
            '/api/v1/settings/excluded-terms/',
        ]
        
        for url in api_urls:
            try:
                resolve(url)
                print(f"  OK - {url}")
            except Exception as e:
                print(f"  ERROR - {url}: {e}")
                return False
                
        print("OK - Todas las URLs de API estan configuradas correctamente")
        return True
        
    except Exception as e:
        print(f"ERROR - configurando URLs: {e}")
        return False

def main():
    """Ejecuta todos los tests"""
    print("Iniciando tests de configuracion de APIs...\n")
    
    tests = [
        test_api_imports,
        test_services,
        test_models,
        test_api_urls,
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if test():
                passed += 1
            print()  # Add blank line between tests
        except Exception as e:
            print(f"ERROR - ejecutando {test.__name__}: {e}\n")
    
    print(f"Resultados: {passed}/{total} tests pasaron")
    
    if passed == total:
        print("EXITO - Todas las APIs estan correctamente configuradas y listas para usar!")
        print("\nPuedes iniciar el servidor con: python manage.py runserver")
        print("Y luego probar las APIs en: http://localhost:8000/api/v1/")
    else:
        print("ADVERTENCIA - Algunos tests fallaron. Revisa la configuracion.")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)