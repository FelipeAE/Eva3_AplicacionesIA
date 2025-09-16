from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.core.paginator import Paginator
from rest_framework.authtoken.models import Token
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated
import json
import logging

from .models import SesionChat, MensajeChat, PreguntaBloqueada, ContextoPrompt, TerminoExcluido, DatosFuenteMensaje
from .services import ChatService, ValidationService
from .bot import guardar_mensaje


# ==================== CHAT APIs ====================

@api_view(['GET'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def api_sessions_list(request):
    """Lista las sesiones del usuario"""
    try:
        page = int(request.GET.get('page', 1))
        per_page = int(request.GET.get('per_page', 10))
        
        sesiones = SesionChat.objects.filter(
            usuario=request.user
        ).order_by('-fecha_inicio')
        
        paginator = Paginator(sesiones, per_page)
        page_obj = paginator.get_page(page)
        
        # Return sessions directly as array for frontend compatibility
        sessions_data = [
            {
                "id": s.id_sesion,
                "nombre": s.nombre_sesion or "(sin nombre)",
                "fecha_creacion": s.fecha_inicio.isoformat() if s.fecha_inicio else None,
                "finalizada": s.estado == 'finalizada',
                "tiene_pregunta_bloqueada": PreguntaBloqueada.objects.filter(sesion=s).exists()
            }
            for s in sesiones
        ]
        
        return JsonResponse(sessions_data, safe=False)
    except Exception as e:
        logging.error(f"Error in api_sessions_list: {e}")
        return JsonResponse({"error": "Error obteniendo sesiones"}, status=500)


@api_view(['POST'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def api_session_create(request):
    """Crea una nueva sesión"""
    try:
        id_sesion = ChatService.create_session(request.user)
        return JsonResponse({
            "success": True,
            "session_id": id_sesion,
            "message": "Sesión creada exitosamente"
        })
    except Exception as e:
        logging.error(f"Error creating session: {e}")
        return JsonResponse({
            "success": False,
            "error": "Error creando sesión"
        }, status=500)


@api_view(['GET'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def api_session_detail(request, session_id):
    """Obtiene detalles de una sesión y sus mensajes"""
    try:
        sesion = get_object_or_404(SesionChat, id_sesion=session_id, usuario=request.user)
        mensajes = MensajeChat.objects.filter(sesion=sesion).order_by('fecha')
        bloqueadas = PreguntaBloqueada.objects.filter(sesion=sesion).exists()
        contexto_activo = ContextoPrompt.objects.filter(activo=True).first()
        
        # Agregar datos fuente a mensajes de IA
        for msg in mensajes:
            if msg.tipo_emisor == "ia":
                try:
                    msg.datos_fuente = msg.datos_fuente  # Force access
                except DatosFuenteMensaje.DoesNotExist:
                    msg.datos_fuente = None
        
        data = {
            "session": {
                "id": sesion.id_sesion,
                "name": sesion.nombre_sesion,
                "status": sesion.estado,
                "created_at": sesion.fecha_inicio.isoformat() if sesion.fecha_inicio else None,
                "finished_at": sesion.fecha_termino.isoformat() if sesion.fecha_termino else None,
                "readonly": sesion.estado == 'finalizada',
                "has_blocked_questions": bloqueadas
            },
            "messages": [
                {
                    "id": m.id_mensaje,
                    "sender": m.tipo_emisor,
                    "content": m.contenido,
                    "timestamp": m.fecha.isoformat() if m.fecha else None,
                    "has_source_data": hasattr(m, 'datos_fuente') and m.datos_fuente is not None,
                    "metadata": m.metadata if hasattr(m, 'metadata') and m.metadata else None
                }
                for m in mensajes
            ],
            "context": {
                "active_context": contexto_activo.nombre if contexto_activo else None
            }
        }
        return JsonResponse(data)
    except Exception as e:
        logging.error(f"Error in api_session_detail: {e}")
        return JsonResponse({"error": "Error obteniendo sesión"}, status=500)


@api_view(['POST'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def api_send_message(request, session_id):
    """Envía un mensaje al chat"""
    try:
        sesion = get_object_or_404(SesionChat, id_sesion=session_id, usuario=request.user)
        
        if sesion.estado == 'finalizada':
            return JsonResponse({
                "success": False,
                "error": "La sesión está finalizada"
            }, status=400)
        
        data = json.loads(request.body)
        pregunta = data.get('message', '').strip()
        
        if not pregunta:
            return JsonResponse({
                "success": False,
                "error": "El mensaje no puede estar vacío"
            }, status=400)
        
        # Sanitizar entrada
        pregunta = ValidationService.sanitize_input(pregunta)
        
        # Guardar mensaje del usuario
        guardar_mensaje(sesion.id_sesion, "usuario", pregunta)
        
        # Procesar mensaje usando el servicio
        result = ChatService.process_message(sesion, pregunta, request.user)
        
        if not result["success"]:
            return JsonResponse({
                "success": False,
                "error": result["message"]
            })
        
        return JsonResponse({
            "success": True,
            "message": "Mensaje procesado exitosamente",
            "response": result["message"],
            "has_source_data": bool(result.get("datos_fuente")),
            "metadata": result.get("ids_extra")
        })
        
    except json.JSONDecodeError:
        return JsonResponse({
            "success": False,
            "error": "Formato JSON inválido"
        }, status=400)
    except Exception as e:
        logging.error(f"Error in api_send_message: {e}")
        return JsonResponse({
            "success": False,
            "error": "Error procesando mensaje"
        }, status=500)


@api_view(['POST'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def api_session_finalize(request, session_id):
    """Finaliza una sesión"""
    try:
        sesion = get_object_or_404(SesionChat, id_sesion=session_id, usuario=request.user)
        
        if sesion.estado == 'finalizada':
            return JsonResponse({
                "success": False,
                "error": "La sesión ya está finalizada"
            })
        
        if ChatService.finalize_session(session_id, request.user.id):
            return JsonResponse({
                "success": True,
                "message": "Sesión finalizada exitosamente"
            })
        else:
            return JsonResponse({
                "success": False,
                "error": "Error finalizando la sesión"
            }, status=500)
            
    except Exception as e:
        logging.error(f"Error in api_session_finalize: {e}")
        return JsonResponse({
            "success": False,
            "error": "Error finalizando sesión"
        }, status=500)


@api_view(['DELETE'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def api_session_delete(request, session_id):
    """Elimina una sesión"""
    try:
        sesion = get_object_or_404(SesionChat, id_sesion=session_id, usuario=request.user)
        
        if not ChatService.can_delete_session(session_id):
            return JsonResponse({
                "success": False,
                "error": "No se puede eliminar esta sesión porque contiene preguntas bloqueadas"
            }, status=400)
        
        if ChatService.delete_session(session_id, request.user):
            return JsonResponse({
                "success": True,
                "message": "Sesión eliminada exitosamente"
            })
        else:
            return JsonResponse({
                "success": False,
                "error": "Error eliminando la sesión"
            }, status=500)
            
    except Exception as e:
        logging.error(f"Error in api_session_delete: {e}")
        return JsonResponse({
            "success": False,
            "error": "Error eliminando sesión"
        }, status=500)


# ==================== ADMIN APIs ====================

@api_view(['GET'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def api_admin_dashboard(request):
    """Dashboard con estadísticas del sistema"""
    try:
        if not request.user.is_staff:
            return JsonResponse({"error": "Acceso denegado"}, status=403)
        
        from django.contrib.auth.models import User
        from django.utils import timezone
        from datetime import timedelta
        from django.db.models import Count
        
        # Estadísticas generales
        total_usuarios = User.objects.count()
        usuarios_activos = User.objects.filter(last_login__gte=timezone.now() - timedelta(days=30)).count()
        total_sesiones = SesionChat.objects.count()
        sesiones_activas = SesionChat.objects.filter(estado='activa').count()
        total_mensajes = MensajeChat.objects.count()
        preguntas_bloqueadas = PreguntaBloqueada.objects.count()
        
        # Usuarios más activos (por número de sesiones)
        usuarios_activos_data = User.objects.annotate(
            num_sesiones=Count('sesionchat')
        ).order_by('-num_sesiones')[:5]
        
        # Sesiones recientes
        sesiones_recientes = SesionChat.objects.select_related('usuario').order_by('-fecha_inicio')[:10]
        
        # Preguntas bloqueadas recientes
        preguntas_bloqueadas_recientes = PreguntaBloqueada.objects.select_related('sesion__usuario').order_by('-fecha')[:5]
        
        # Términos más excluidos
        terminos_frecuentes = TerminoExcluido.objects.values('palabra').annotate(
            count=Count('palabra')
        ).order_by('-count')[:10]
        
        # Contexto activo
        contexto_activo = ContextoPrompt.objects.filter(activo=True).first()
        
        data = {
            "statistics": {
                "total_usuarios": total_usuarios,
                "usuarios_activos": usuarios_activos,
                "total_sesiones": total_sesiones,
                "sesiones_activas": sesiones_activas,
                "total_mensajes": total_mensajes,
                "preguntas_bloqueadas": preguntas_bloqueadas,
            },
            "active_users": [
                {
                    "id": u.id,
                    "username": u.username,
                    "num_sesiones": u.num_sesiones,
                    "last_login": u.last_login.isoformat() if u.last_login else None
                }
                for u in usuarios_activos_data
            ],
            "recent_sessions": [
                {
                    "id": s.id_sesion,
                    "name": s.nombre_sesion,
                    "user": s.usuario.username if s.usuario else "N/A",
                    "created": s.fecha_inicio.isoformat() if s.fecha_inicio else None,
                    "status": s.estado
                }
                for s in sesiones_recientes
            ],
            "blocked_questions": [
                {
                    "id": p.id,
                    "question": p.pregunta,
                    "reason": p.razon,
                    "user": p.sesion.usuario.username if p.sesion and p.sesion.usuario else "N/A",
                    "date": p.fecha.isoformat() if p.fecha else None
                }
                for p in preguntas_bloqueadas_recientes
            ],
            "frequent_excluded_terms": [
                {
                    "term": t['palabra'],
                    "count": t['count']
                }
                for t in terminos_frecuentes
            ],
            "active_context": {
                "id": contexto_activo.id,
                "nombre": contexto_activo.nombre,
                "prompt": contexto_activo.prompt_sistema,
                "activo": contexto_activo.activo,
                "fecha_creacion": str(contexto_activo.id)  # Placeholder, agregar campo si es necesario
            } if contexto_activo else None
        }
        
        return JsonResponse(data)
    
    except Exception as e:
        logging.error(f"Error in api_admin_dashboard: {e}")
        return JsonResponse({"error": "Error obteniendo dashboard"}, status=500)


@api_view(['GET'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def api_contexts_list(request):
    """Lista todos los contextos (solo admin)"""
    # Check if user is staff
    if not request.user.is_staff:
        return JsonResponse({"error": "No tienes permisos para acceder a esta función"}, status=403)
    try:
        contextos = ContextoPrompt.objects.all().order_by('-id')
        data = [
            {
                "id": c.id,
                "nombre": c.nombre,
                "activo": c.activo,
                "prompt": c.prompt_sistema,
                "fecha_creacion": None  # No existe este campo en el modelo actual
            }
            for c in contextos
        ]
        return JsonResponse(data, safe=False)
    except Exception as e:
        logging.error(f"Error in api_contexts_list: {e}")
        return JsonResponse({"error": "Error obteniendo contextos"}, status=500)


@api_view(['POST'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def api_context_create(request):
    """Crea un nuevo contexto (solo admin)"""
    # Check if user is staff
    if not request.user.is_staff:
        return JsonResponse({"error": "No tienes permisos para acceder a esta función"}, status=403)
    try:
        data = json.loads(request.body)
        nombre = data.get('nombre', '').strip()
        prompt_sistema = data.get('prompt', '').strip()
        
        if not nombre or not prompt_sistema:
            return JsonResponse({
                "success": False,
                "error": "Nombre y prompt son requeridos"
            }, status=400)
        
        contexto = ContextoPrompt.objects.create(
            nombre=nombre,
            prompt_sistema=prompt_sistema
        )
        
        return JsonResponse({
            "success": True,
            "message": "Contexto creado exitosamente",
            "context_id": contexto.id
        })
        
    except json.JSONDecodeError:
        return JsonResponse({
            "success": False,
            "error": "Formato JSON inválido"
        }, status=400)
    except Exception as e:
        logging.error(f"Error in api_context_create: {e}")
        return JsonResponse({
            "success": False,
            "error": "Error creando contexto"
        }, status=500)


@api_view(['POST'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def api_context_activate(request, context_id):
    """Activa un contexto (solo admin)"""
    # Check if user is staff
    if not request.user.is_staff:
        return JsonResponse({"error": "No tienes permisos para acceder a esta función"}, status=403)
    try:
        contexto = get_object_or_404(ContextoPrompt, id=context_id)
        
        # Desactivar todos y activar solo este
        ContextoPrompt.objects.update(activo=False)
        contexto.activo = True
        contexto.save()
        
        return JsonResponse({
            "success": True,
            "message": f"Contexto '{contexto.nombre}' activado exitosamente"
        })
        
    except Exception as e:
        logging.error(f"Error in api_context_activate: {e}")
        return JsonResponse({
            "success": False,
            "error": "Error activando contexto"
        }, status=500)


@api_view(['POST'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def api_context_deactivate(request, context_id):
    """Desactiva un contexto (solo admin)"""
    # Check if user is staff
    if not request.user.is_staff:
        return JsonResponse({"error": "No tienes permisos para acceder a esta función"}, status=403)
    try:
        contexto = get_object_or_404(ContextoPrompt, id=context_id)
        contexto.activo = False
        contexto.save()
        
        return JsonResponse({
            "success": True,
            "message": f"Contexto '{contexto.nombre}' desactivado exitosamente"
        })
        
    except Exception as e:
        logging.error(f"Error in api_context_deactivate: {e}")
        return JsonResponse({
            "success": False,
            "error": "Error desactivando contexto"
        }, status=500)


@api_view(['DELETE'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def api_context_delete(request, context_id):
    """Elimina un contexto (solo admin)"""
    # Check if user is staff
    if not request.user.is_staff:
        return JsonResponse({"error": "No tienes permisos para acceder a esta función"}, status=403)
    try:
        contexto = get_object_or_404(ContextoPrompt, id=context_id)
        nombre = contexto.nombre
        contexto.delete()
        
        return JsonResponse({
            "success": True,
            "message": f"Contexto '{nombre}' eliminado exitosamente"
        })
        
    except Exception as e:
        logging.error(f"Error in api_context_delete: {e}")
        return JsonResponse({
            "success": False,
            "error": "Error eliminando contexto"
        }, status=500)


# ==================== USER SETTINGS APIs ====================

@api_view(['GET'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def api_excluded_terms(request):
    """Lista términos excluidos del usuario"""
    try:
        terminos = TerminoExcluido.objects.filter(usuario=request.user).order_by('-id')
        data = [
            {
                "id": t.id,
                "termino": t.palabra,
                "fecha_creacion": None  # No existe este campo en el modelo actual
            }
            for t in terminos
        ]
        return JsonResponse(data, safe=False)
    except Exception as e:
        logging.error(f"Error in api_excluded_terms: {e}")
        return JsonResponse({"error": "Error obteniendo términos excluidos"}, status=500)


@api_view(['POST'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def api_excluded_term_add(request):
    """Agrega un término excluido"""
    try:
        data = json.loads(request.body)
        termino = data.get('termino', '').strip().lower()
        
        if not termino:
            return JsonResponse({
                "success": False,
                "error": "El término no puede estar vacío"
            }, status=400)
        
        # Verificar si ya existe
        if TerminoExcluido.objects.filter(usuario=request.user, palabra=termino).exists():
            return JsonResponse({
                "success": False,
                "error": "El término ya existe"
            }, status=400)
        
        TerminoExcluido.objects.create(usuario=request.user, palabra=termino)
        
        return JsonResponse({
            "success": True,
            "message": f"Término '{termino}' agregado exitosamente"
        })
        
    except json.JSONDecodeError:
        return JsonResponse({
            "success": False,
            "error": "Formato JSON inválido"
        }, status=400)
    except Exception as e:
        logging.error(f"Error in api_excluded_term_add: {e}")
        return JsonResponse({
            "success": False,
            "error": "Error agregando término"
        }, status=500)


@api_view(['DELETE'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def api_excluded_term_delete(request, term_id):
    """Elimina un término excluido"""
    try:
        termino = get_object_or_404(TerminoExcluido, id=term_id, usuario=request.user)
        palabra = termino.palabra
        termino.delete()
        
        return JsonResponse({
            "success": True,
            "message": f"Término '{palabra}' eliminado exitosamente"
        })
        
    except Exception as e:
        logging.error(f"Error in api_excluded_term_delete: {e}")
        return JsonResponse({
            "success": False,
            "error": "Error eliminando término"
        }, status=500)


# ==================== AUTH APIs ====================

@csrf_exempt
@require_http_methods(["POST"])
def api_login(request):
    """Login endpoint que retorna token de autenticación"""
    try:
        data = json.loads(request.body)
        username = data.get('username')
        password = data.get('password')
        
        if not username or not password:
            return JsonResponse({
                "error": "Username y password son requeridos"
            }, status=400)
        
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            token, created = Token.objects.get_or_create(user=user)
            
            return JsonResponse({
                "token": token.key,
                "user": {
                    "id": user.id,
                    "username": user.username,
                    "is_staff": user.is_staff
                }
            })
        else:
            return JsonResponse({
                "error": "Credenciales inválidas"
            }, status=401)
            
    except json.JSONDecodeError:
        return JsonResponse({
            "error": "Formato JSON inválido"
        }, status=400)
    except Exception as e:
        logging.error(f"Error in api_login: {e}")
        return JsonResponse({
            "error": "Error interno del servidor"
        }, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def api_logout(request):
    """Logout endpoint"""
    try:
        if request.user.is_authenticated:
            # Eliminar el token del usuario
            Token.objects.filter(user=request.user).delete()
            logout(request)
        
        return JsonResponse({
            "message": "Logout exitoso"
        })
        
    except Exception as e:
        logging.error(f"Error in api_logout: {e}")
        return JsonResponse({
            "error": "Error durante logout"
        }, status=500)


@login_required
@require_http_methods(["GET"])
def api_auth_check(request):
    """Verifica si el usuario está autenticado y retorna sus datos"""
    try:
        return JsonResponse({
            "id": request.user.id,
            "username": request.user.username,
            "is_staff": request.user.is_staff
        })
        
    except Exception as e:
        logging.error(f"Error in api_auth_check: {e}")
        return JsonResponse({
            "error": "Error verificando autenticación"
        }, status=500)