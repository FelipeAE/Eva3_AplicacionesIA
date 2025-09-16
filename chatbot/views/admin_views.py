from django.shortcuts import render, redirect
from django.contrib.admin.views.decorators import staff_member_required
from django.utils import timezone
from django.db.models import Count
from django.contrib.auth.models import User
from datetime import timedelta

from ..models import SesionChat, MensajeChat, PreguntaBloqueada, ContextoPrompt, TerminoExcluido


@staff_member_required
def gestionar_contextos(request):
    if request.method == "POST":
        if "activar" in request.POST:
            contexto = ContextoPrompt.objects.get(id=request.POST["activar"])
            ContextoPrompt.objects.update(activo=False)
            ContextoPrompt.objects.filter(id=request.POST["activar"]).update(activo=True)
            from django.contrib import messages
            messages.success(request, f'✅ Contexto "{contexto.nombre}" activado: {contexto.prompt_sistema[:100]}...')
        elif "desactivar" in request.POST:
            contexto = ContextoPrompt.objects.get(id=request.POST["desactivar"])
            ContextoPrompt.objects.filter(id=request.POST["desactivar"]).update(activo=False)
            from django.contrib import messages
            messages.warning(request, f'⚠️ Contexto "{contexto.nombre}" desactivado. Se usará el contexto por defecto.')
        elif "crear" in request.POST:
            nombre = request.POST.get("nombre", "").strip()
            texto = request.POST.get("prompt_sistema", "").strip()
            if nombre and texto:
                ContextoPrompt.objects.create(nombre=nombre, prompt_sistema=texto)
                from django.contrib import messages
                messages.success(request, f'✅ Contexto "{nombre}" creado exitosamente.')
        elif "eliminar" in request.POST:
            contexto = ContextoPrompt.objects.get(id=request.POST["eliminar"])
            ContextoPrompt.objects.filter(id=request.POST["eliminar"]).delete()
            from django.contrib import messages
            messages.error(request, f'🗑️ Contexto "{contexto.nombre}" eliminado.')
        return redirect('gestionar_contextos')

    contextos = ContextoPrompt.objects.all()
    return render(request, 'chatbot/contextos.html', {"contextos": contextos})


@staff_member_required
def panel_admin(request):
    """Panel de administración completo"""
    
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
    
    # Contextos disponibles
    contextos = ContextoPrompt.objects.all()
    
    # Contexto activo
    contexto_activo = ContextoPrompt.objects.filter(activo=True).first()
    
    # Términos más excluidos
    terminos_frecuentes = TerminoExcluido.objects.values('palabra').annotate(
        count=Count('palabra')
    ).order_by('-count')[:10]
    
    context = {
        'total_usuarios': total_usuarios,
        'usuarios_activos': usuarios_activos,
        'total_sesiones': total_sesiones,
        'sesiones_activas': sesiones_activas,
        'total_mensajes': total_mensajes,
        'preguntas_bloqueadas': preguntas_bloqueadas,
        'usuarios_activos_data': usuarios_activos_data,
        'sesiones_recientes': sesiones_recientes,
        'preguntas_bloqueadas_recientes': preguntas_bloqueadas_recientes,
        'contextos': contextos,
        'contexto_activo': contexto_activo,
        'terminos_frecuentes': terminos_frecuentes,
    }
    
    return render(request, 'chatbot/admin_panel.html', context)