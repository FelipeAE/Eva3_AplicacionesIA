from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import Persona, Funcion, TiempoContrato, Contrato
from .models import SesionChat, MensajeChat, PreguntaBloqueada
from .models import ContextoPrompt, DatosFuenteMensaje, TerminoExcluido
from django.contrib.admin.views.decorators import staff_member_required
from django.utils import timezone
from django.db.models import Count, Q
from django.db import connection
from .bot import obtener_consulta_sql, generar_respuesta_final, es_pregunta_valida, guardar_mensaje
from django.http import JsonResponse
import re
import json
from django.forms.models import model_to_dict
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login
from django.contrib import messages
from django.contrib.auth.models import User
from datetime import timedelta

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
        if pregunta:
            # Guardar mensaje del usuario
            guardar_mensaje(sesion.id_sesion, "usuario", pregunta)
            

            # Validar
            es_valida, razon = es_pregunta_valida(pregunta)
            if not es_valida:
                advertencia = "⚠️ Tu pregunta no está relacionada con recursos humanos universitarios."
                MensajeChat.objects.create(
                    sesion=sesion,
                    tipo_emisor="ia",
                    contenido=advertencia,
                    fecha=timezone.now()
                )
                PreguntaBloqueada.objects.create(
                    sesion=sesion,
                    pregunta=pregunta,
                    razon=razon,
                    fecha=timezone.now()
                )
                return redirect('chat_sesion', id=id)

            # Obtener términos excluidos del usuario
            terminos_excluidos = list(TerminoExcluido.objects.filter(usuario=request.user).values_list("palabra", flat=True))

            # Obtener historial
            historial = [
                {"role": "user" if m.tipo_emisor == "usuario" else "assistant", "content": m.contenido}
                for m in mensajes
            ]

            # Generar SQL y respuesta (pasando términos excluidos)
            sql_query = obtener_consulta_sql(pregunta, historial, terminos_excluidos)

            if not sql_query.lower().startswith("select"):
                MensajeChat.objects.create(
                    sesion=sesion,
                    tipo_emisor="ia",
                    contenido="⚠️ Se detectó una combinación de palabras incoherentes. Intenta reformular la pregunta.",
                    fecha=timezone.now()
                )
                return redirect('chat_sesion', id=id)

            with connection.cursor() as cur:
                cur.execute(sql_query)
                columnas = [desc[0] for desc in cur.description]
                filas = [dict(zip(columnas, row)) for row in cur.fetchall()]

            respuesta, tipo_relacionado, ids_relacionados = generar_respuesta_final(pregunta, filas, historial)
            
            # Buscar un ID insertado por Claude
            match = re.search(r"\{.*?\}", respuesta)
            ids_extra = None
            if match:
                try:
                    ids_extra = json.loads(match.group())
                except json.JSONDecodeError:
                    pass
                
            
            # Guardar la respuesta sin el bloque JSON final
            respuesta_limpia = respuesta.replace(match.group(), "").strip() if match else respuesta

            mensaje = MensajeChat.objects.create(
                sesion=sesion,
                tipo_emisor="ia",
                contenido=respuesta,
                fecha=timezone.now()
            )
            
            # Nueva parte: guardar datos fuente
            metadata = {}
            if ids_relacionados:
                metadata["tipo"] = tipo_relacionado
                metadata["ids"] = ids_relacionados
                
            if metadata:
                mensaje.metadata = metadata
                mensaje.save()
            
            # NUEVO: Guardar datos fuente separados
            if filas:
                json_valido = json.dumps(filas)
                DatosFuenteMensaje.objects.create(mensaje=mensaje, datos=json_valido)
            
            if ids_extra:
                request.session['detalles'] = ids_extra
                
            request.session['datos_fuente'] = filas

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
    from django.db import connection
    with connection.cursor() as cur:
        cur.execute(
            "INSERT INTO sesion_chat (fecha_inicio, estado, nombre_sesion, usuario_id) VALUES (NOW(), 'activa', %s, %s) RETURNING id_sesion",
            ["Sesión nueva", request.user.id]
        )
        id_sesion = cur.fetchone()[0]
    return redirect('chat_sesion', id=id_sesion)


@login_required
def borrar_sesion(request, id):
    # Verificar que la sesión pertenece al usuario
    sesion = get_object_or_404(SesionChat, id_sesion=id, usuario=request.user)
    
    if PreguntaBloqueada.objects.filter(sesion_id=id).exists():
        return render(request, 'chatbot/no_borrar.html')
    MensajeChat.objects.filter(sesion_id=id).delete()
    SesionChat.objects.filter(id_sesion=id, usuario=request.user).delete()
    return redirect('chat_home')

@login_required
def finalizar_sesion(request, id):
    sesion = get_object_or_404(SesionChat, id_sesion=id, usuario=request.user)
    if sesion.estado != 'finalizada':
        with connection.cursor() as cur:
            cur.execute(
                "UPDATE sesion_chat SET estado = 'finalizada', fecha_termino = NOW() WHERE id_sesion = %s AND usuario_id = %s",
                [id, request.user.id]
            )
    return redirect('chat_sesion', id=id)

@login_required
def excluir_terminos(request):
    from .models import TerminoExcluido
    if request.method == "POST":
        nuevo = request.POST.get("nuevo_termino", "").strip()
        if nuevo:
            TerminoExcluido.objects.get_or_create(usuario=request.user, palabra=nuevo)
        eliminar = request.POST.getlist("eliminar")
        TerminoExcluido.objects.filter(usuario=request.user, palabra__in=eliminar).delete()
        return redirect('excluir_terminos')

    terminos = TerminoExcluido.objects.filter(usuario=request.user)
    return render(request, 'chatbot/excluir.html', {'terminos': terminos})


@staff_member_required
def gestionar_contextos(request):
    if request.method == "POST":
        if "activar" in request.POST:
            ContextoPrompt.objects.update(activo=False)
            ContextoPrompt.objects.filter(id=request.POST["activar"]).update(activo=True)
        elif "crear" in request.POST:
            nombre = request.POST.get("nombre", "").strip()
            texto = request.POST.get("prompt_sistema", "").strip()
            if nombre and texto:
                ContextoPrompt.objects.create(nombre=nombre, prompt_sistema=texto)
        elif "eliminar" in request.POST:
            ContextoPrompt.objects.filter(id=request.POST["eliminar"]).delete()
        return redirect('gestionar_contextos')

    contextos = ContextoPrompt.objects.all()
    return render(request, 'chatbot/contextos.html', {"contextos": contextos})

@login_required
def detalle_contrato(request, id):
    contrato = get_object_or_404(Contrato, id_contrato=id)
    data = {
        "id": contrato.id_contrato,
        "honorario_total_bruto": contrato.honorario_total_bruto,
        "tipo_pago": contrato.tipo_pago,
        "viaticos": contrato.viaticos,
        "observaciones": contrato.observaciones,
        "enlace_funciones": contrato.enlace_funciones,
        "persona": contrato.persona.nombre_completo,
        "funcion": contrato.funcion.descripcion_funcion,
        "calificacion": contrato.funcion.calificacion_profesional,
        "mes": contrato.tiempo.mes,
        "anho": contrato.tiempo.anho,
        "region": contrato.tiempo.region,
    }
    return JsonResponse(data)

@login_required
def detalle_generico(request, tipo, id):
    # Normalizar tipo (e.g., id_personas → persona)
    tipo_normalizado = tipo.replace("id_", "").rstrip("s")

    modelos = {
        "persona": Persona,
        "funcion": Funcion,
        "tiempo": TiempoContrato,
        "contrato": Contrato,
    }

    if tipo_normalizado not in modelos:
        return JsonResponse({"error": "Tipo no reconocido"}, status=400)

    modelo = modelos[tipo_normalizado]
    obj = get_object_or_404(modelo, pk=id)
    data = model_to_dict(obj)

    # Relaciones legibles si es contrato
    if tipo_normalizado == "contrato":
        data["persona"] = obj.persona.nombre_completo
        data["funcion"] = obj.funcion.descripcion_funcion
        data["tiempo"] = f"{obj.tiempo.mes} {obj.tiempo.anho}"

    return JsonResponse(data)

def registro(request):
    if request.method == "POST":
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            username = form.cleaned_data.get('username')
            messages.success(request, f"Usuario {username} creado exitosamente.")
            login(request, user)  # Login automático después del registro
            return redirect('chat_home')
    else:
        form = UserCreationForm()
    return render(request, 'registration/registro.html', {'form': form})

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
        'terminos_frecuentes': terminos_frecuentes,
    }
    
    return render(request, 'chatbot/admin_panel.html', context)




