from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import Persona, Funcion, TiempoContrato, Contrato
from .models import SesionChat, MensajeChat, PreguntaBloqueada
from django.utils import timezone
from django.db.models import Count
from django.db import connection
from .bot import obtener_consulta_sql, generar_respuesta_final, es_pregunta_valida, guardar_mensaje

@login_required
def chat_home(request):
    sesiones = SesionChat.objects.all().order_by('-fecha_inicio')[:10]
    return render(request, 'chatbot/home.html', {'sesiones': sesiones})

@login_required
def chat_sesion(request, id):
    sesion = get_object_or_404(SesionChat, id_sesion=id)
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

            # Obtener historial
            historial = [
                {"role": "user" if m.tipo_emisor == "usuario" else "assistant", "content": m.contenido}
                for m in mensajes
            ]

            # Generar SQL y respuesta
            sql_query = obtener_consulta_sql(pregunta, historial)

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

            respuesta = generar_respuesta_final(pregunta, filas, historial)

            MensajeChat.objects.create(
                sesion=sesion,
                tipo_emisor="ia",
                contenido=respuesta,
                fecha=timezone.now()
            )

            return redirect('chat_sesion', id=id)

    return render(request, 'chatbot/sesion.html', {
        'sesion': sesion,
        'mensajes': mensajes,
        'bloqueadas': bloqueadas,
        'solo_lectura': solo_lectura,
    })


@login_required
def nueva_sesion(request):
    from django.db import connection
    with connection.cursor() as cur:
        cur.execute(
            "INSERT INTO sesion_chat (fecha_inicio, estado, nombre_sesion) VALUES (NOW(), 'activa', %s) RETURNING id_sesion",
            ["Sesión nueva"]
        )
        id_sesion = cur.fetchone()[0]
    return redirect('chat_sesion', id=id_sesion)


@login_required
def borrar_sesion(request, id):
    if PreguntaBloqueada.objects.filter(sesion_id=id).exists():
        return render(request, 'chatbot/no_borrar.html')
    MensajeChat.objects.filter(sesion_id=id).delete()
    SesionChat.objects.filter(id_sesion=id).delete()
    return redirect('chat_home')

@login_required
def finalizar_sesion(request, id):
    sesion = get_object_or_404(SesionChat, id_sesion=id)
    if sesion.estado != 'finalizada':
        with connection.cursor() as cur:
            cur.execute(
                "UPDATE sesion_chat SET estado = 'finalizada', fecha_termino = NOW() WHERE id_sesion = %s",
                [id]
            )
    return redirect('chat_sesion', id=id)

