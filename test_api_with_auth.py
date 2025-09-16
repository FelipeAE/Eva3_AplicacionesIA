#!/usr/bin/env python
"""
Script para probar las APIs con autenticacin de Django
"""

import os
import django
import requests

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'chatbot_web.settings')
django.setup()

# Importar despus de configurar Django
from django.test import Client
from django.contrib.auth.models import User

def test_with_django_client():
    """Probar APIs usando Django Test Client (simula autenticacin)"""
    print("Testing APIs with Django Test Client...\n")
    
    # Crear cliente de test
    client = Client()
    
    # Crear o obtener usuario de prueba
    user, created = User.objects.get_or_create(
        username='testuser',
        defaults={'email': 'test@example.com'}
    )
    if created:
        user.set_password('testpass123')
        user.save()
        print(f" Created test user: {user.username}")
    else:
        print(f" Using existing test user: {user.username}")
    
    # Login
    client.force_login(user)
    print(" User logged in")
    
    print("\n" + "="*50)
    print(" TEST 1: List Sessions")
    print("="*50)
    
    response = client.get('/api/v1/sessions/')
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(" Sessions API works!")
        print(f"Sessions count: {len(data.get('sessions', []))}")
        print(f"Response: {data}")
    else:
        print(f" Error: {response.content}")
    
    print("\n" + "="*50)
    print(" TEST 2: Create Session")
    print("="*50)
    
    response = client.post('/api/v1/sessions/create/')
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(" Create session API works!")
        session_id = data.get('session_id')
        print(f"New session ID: {session_id}")
        
        if session_id:
            print("\n" + "="*50)
            print(" TEST 3: Get Session Details")
            print("="*50)
            
            response = client.get(f'/api/v1/sessions/{session_id}/')
            print(f"Status: {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                print(" Get session details API works!")
                print(f"Session name: {data['session']['name']}")
                print(f"Messages count: {len(data.get('messages', []))}")
            else:
                print(f" Error: {response.content}")
            
            print("\n" + "="*50)
            print(" TEST 4: Send Message")
            print("="*50)
            
            response = client.post(
                f'/api/v1/sessions/{session_id}/message/',
                data='{"message": "Dame el top 5 de honorarios"}',
                content_type='application/json'
            )
            print(f"Status: {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                print(" Send message API works!")
                print(f"Success: {data.get('success')}")
                print(f"Response preview: {data.get('response', '')[:100]}...")
            else:
                data = response.json() if response.content else {}
                print(f" Error: {data.get('error', response.content)}")
    else:
        print(f" Error creating session: {response.content}")
    
    # Test Admin APIs (if user is staff)
    if user.is_staff:
        print("\n" + "="*50)
        print(" TEST 5: List Contexts (Admin)")
        print("="*50)
        
        response = client.get('/api/v1/admin/contexts/')
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(" List contexts API works!")
            print(f"Contexts count: {len(data.get('contexts', []))}")
        else:
            print(f" Error: {response.content}")
    else:
        print("\n  User is not staff - skipping admin tests")
        print("To test admin APIs, run: python manage.py shell")
        print("Then: User.objects.filter(username='testuser').update(is_staff=True)")
    
    print("\n" + "="*50)
    print(" TEST 6: Excluded Terms")
    print("="*50)
    
    response = client.get('/api/v1/settings/excluded-terms/')
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(" Excluded terms API works!")
        print(f"Excluded terms count: {len(data.get('excluded_terms', []))}")
        
        # Try to add a term
        response = client.post(
            '/api/v1/settings/excluded-terms/add/',
            data='{"term": "test_api"}',
            content_type='application/json'
        )
        print(f"Add term status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f" Add term result: {data.get('message')}")
        else:
            data = response.json() if response.content else {}
            print(f"  Add term result: {data.get('error', 'Unknown error')}")
    else:
        print(f" Error: {response.content}")

def test_server_running():
    """Verificar que el servidor est funcionando"""
    print(" Testing server connectivity...\n")
    
    try:
        response = requests.get('http://localhost:8000/', timeout=5)
        print(f" Server is running! Status: {response.status_code}")
        return True
    except requests.exceptions.ConnectionError:
        print(" Server is not running!")
        print("Please run: python manage.py runserver")
        return False
    except Exception as e:
        print(f" Error connecting to server: {e}")
        return False

if __name__ == "__main__":
    print(" API Testing with Authentication\n")
    
    if test_server_running():
        print()
        test_with_django_client()
        
        print("\n" + "="*60)
        print(" API Testing Complete!")
        print("="*60)
        print("\nNext steps:")
        print("1. Open http://localhost:8000 and login")
        print("2. Open api_test.html in your browser to test APIs manually")
        print("3. APIs are ready for React frontend!")
    else:
        print("\n Cannot test APIs - server not running")