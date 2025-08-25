from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.core.paginator import Paginator
import json
import logging

from .models import SesionChat, MensajeChat, PreguntaBloqueada, ContextoPrompt, TerminoExcluido, DatosFuenteMensaje
from .services import ChatService, ValidationService
from .bot import guardar_mensaje


# ==================== CHAT APIs ====================

@login_required
@require_http_methods(["GET"])
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
        
        data = {
            "sessions": [
                {
                    "id": s.id_sesion,
                    "name": s.nombre_sesion or "(sin nombre)",
                    "status": s.estado,
                    "created_at": s.fecha_inicio.isoformat() if s.fecha_inicio else None,
                    "finished_at": s.fecha_termino.isoformat() if s.fecha_termino else None,
                }
                for s in page_obj
            ],
            "pagination": {
                "current_page": page_obj.number,
                "total_pages": paginator.num_pages,
                "has_next": page_obj.has_next(),
                "has_previous": page_obj.has_previous(),
                "total_count": paginator.count
            }
        }
        return JsonResponse(data)
    except Exception as e:
        logging.error(f"Error in api_sessions_list: {e}")
        return JsonResponse({"error": "Error obteniendo sesiones"}, status=500)


@login_required
@csrf_exempt
@require_http_methods(["POST"])
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


@login_required
@require_http_methods(["GET"])
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
                    "has_source_data": hasattr(m, 'datos_fuente') and m.datos_fuente is not None
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


@login_required
@csrf_exempt
@require_http_methods(["POST"])
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


@login_required
@csrf_exempt
@require_http_methods(["POST"])
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


@login_required
@csrf_exempt
@require_http_methods(["DELETE"])
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

@staff_member_required
@require_http_methods(["GET"])
def api_contexts_list(request):
    """Lista todos los contextos (solo admin)"""
    try:
        contextos = ContextoPrompt.objects.all()
        data = {
            "contexts": [
                {
                    "id": c.id,
                    "name": c.nombre,
                    "active": c.activo,
                    "prompt": c.prompt_sistema
                }
                for c in contextos
            ]
        }
        return JsonResponse(data)
    except Exception as e:
        logging.error(f"Error in api_contexts_list: {e}")
        return JsonResponse({"error": "Error obteniendo contextos"}, status=500)


@staff_member_required
@csrf_exempt
@require_http_methods(["POST"])
def api_context_create(request):
    """Crea un nuevo contexto (solo admin)"""
    try:
        data = json.loads(request.body)
        nombre = data.get('name', '').strip()
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
            "context": {
                "id": contexto.id,
                "name": contexto.nombre,
                "active": contexto.activo
            }
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


@staff_member_required
@csrf_exempt
@require_http_methods(["POST"])
def api_context_activate(request, context_id):
    """Activa un contexto (solo admin)"""
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


@staff_member_required
@csrf_exempt
@require_http_methods(["POST"])
def api_context_deactivate(request, context_id):
    """Desactiva un contexto (solo admin)"""
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


@staff_member_required
@csrf_exempt
@require_http_methods(["DELETE"])
def api_context_delete(request, context_id):
    """Elimina un contexto (solo admin)"""
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

@login_required
@require_http_methods(["GET"])
def api_excluded_terms(request):
    """Lista términos excluidos del usuario"""
    try:
        terminos = TerminoExcluido.objects.filter(usuario=request.user).order_by('palabra')
        data = {
            "excluded_terms": [
                {
                    "id": t.id,
                    "term": t.palabra
                }
                for t in terminos
            ]
        }
        return JsonResponse(data)
    except Exception as e:
        logging.error(f"Error in api_excluded_terms: {e}")
        return JsonResponse({"error": "Error obteniendo términos excluidos"}, status=500)


@login_required
@csrf_exempt
@require_http_methods(["POST"])
def api_excluded_term_add(request):
    """Agrega un término excluido"""
    try:
        data = json.loads(request.body)
        termino = data.get('term', '').strip().lower()
        
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


@login_required
@csrf_exempt
@require_http_methods(["DELETE"])
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