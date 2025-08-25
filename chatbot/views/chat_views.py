from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.contrib import messages
import logging

from ..models import SesionChat, MensajeChat, PreguntaBloqueada, ContextoPrompt, DatosFuenteMensaje
from ..services import ChatService, ValidationService
from ..bot import guardar_mensaje


@login_required
def chat_home(request):
    sesiones = SesionChat.objects.filter(usuario=request.user).order_by('-fecha_inicio')[:10]
    return render(request, 'chatbot/home.html', {'sesiones': sesiones})


@login_required
def chat_sesion(request, id):
    sesion = get_object_or_404(SesionChat, id_sesion=id, usuario=request.user)
    solo_lectura = sesion.estado == 'finalizada'
    mensajes = MensajeChat.objects.filter(sesion=sesion).order_by('fecha')
    bloqueadas = PreguntaBloqueada.objects.filter(sesion=sesion).exists()

    if request.method == "POST" and not solo_lectura:
        pregunta = request.POST.get("pregunta", "").strip()
        if not pregunta:
            messages.error(request, "Por favor ingresa una pregunta.")
            return redirect('chat_sesion', id=id)
        
        # Sanitizar entrada
        pregunta = ValidationService.sanitize_input(pregunta)
        
        try:
            # Guardar mensaje del usuario
            guardar_mensaje(sesion.id_sesion, "usuario", pregunta)
            
            # Procesar mensaje usando el servicio
            result = ChatService.process_message(sesion, pregunta, request.user)
            
            if not result["success"]:
                messages.warning(request, result["message"])
                return redirect('chat_sesion', id=id)
            
            # Guardar datos en sesión para la vista
            if result.get("datos_fuente"):
                request.session['datos_fuente'] = result["datos_fuente"]
            
            if result.get("ids_extra"):
                request.session['detalles'] = result["ids_extra"]
            
        except Exception as e:
            logging.error(f"Error processing message in chat_sesion: {e}")
            messages.error(request, "Ocurrió un error procesando tu pregunta. Intenta nuevamente.")
            
        return redirect('chat_sesion', id=id)
        
    contexto_activo = ContextoPrompt.objects.filter(activo=True).first()
    
    datos_fuente = request.session.pop('datos_fuente', None)
    
    for msg in mensajes:
        if msg.tipo_emisor == "ia":
            try:
                msg.datos_fuente = msg.datos_fuente #fuerza el acceso
            except DatosFuenteMensaje.DoesNotExist:
                msg.datos_fuente = None

    return render(request, 'chatbot/sesion.html', {
        'sesion': sesion,
        'mensajes': mensajes,
        'bloqueadas': bloqueadas,
        'solo_lectura': solo_lectura,
        'contexto_activo': contexto_activo,
        'datos_fuente': datos_fuente,
    })


@login_required
def nueva_sesion(request):
    try:
        id_sesion = ChatService.create_session(request.user)
        return redirect('chat_sesion', id=id_sesion)
    except Exception as e:
        logging.error(f"Error creating new session: {e}")
        messages.error(request, "Error creando nueva sesión. Intenta nuevamente.")
        return redirect('chat_home')


@login_required
def borrar_sesion(request, id):
    try:
        # Verificar que la sesión pertenece al usuario
        sesion = get_object_or_404(SesionChat, id_sesion=id, usuario=request.user)
        
        if not ChatService.can_delete_session(id):
            return render(request, 'chatbot/no_borrar.html')
        
        if ChatService.delete_session(id, request.user):
            messages.success(request, "Sesión eliminada correctamente.")
        else:
            messages.error(request, "Error eliminando la sesión.")
            
    except Exception as e:
        logging.error(f"Error deleting session: {e}")
        messages.error(request, "Error eliminando la sesión.")
    
    return redirect('chat_home')


@login_required
def finalizar_sesion(request, id):
    try:
        sesion = get_object_or_404(SesionChat, id_sesion=id, usuario=request.user)
        
        if sesion.estado != 'finalizada':
            if ChatService.finalize_session(id, request.user.id):
                messages.success(request, "Sesión finalizada correctamente.")
            else:
                messages.error(request, "Error finalizando la sesión.")
                
    except Exception as e:
        logging.error(f"Error finalizing session: {e}")
        messages.error(request, "Error finalizando la sesión.")
    
    return redirect('chat_sesion', id=id)