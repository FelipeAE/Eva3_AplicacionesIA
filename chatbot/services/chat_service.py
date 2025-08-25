from django.utils import timezone
from django.db import connection
import json
import re
import logging

from ..models import SesionChat, MensajeChat, PreguntaBloqueada, DatosFuenteMensaje, TerminoExcluido
from .validation_service import ValidationService
from .ai_service import AIService


class ChatService:
    """Servicio para manejar la lógica de negocio del chat"""
    
    @staticmethod
    def create_session(user):
        """Crea una nueva sesión de chat"""
        try:
            with connection.cursor() as cur:
                cur.execute(
                    "INSERT INTO sesion_chat (fecha_inicio, estado, nombre_sesion, usuario_id) VALUES (NOW(), 'activa', %s, %s) RETURNING id_sesion",
                    ["Sesión nueva", user.id]
                )
                id_sesion = cur.fetchone()[0]
            return id_sesion
        except Exception as e:
            logging.error(f"Error creating session: {e}")
            raise
    
    @staticmethod
    def process_message(sesion, pregunta, user):
        """Procesa un mensaje del usuario y genera la respuesta de la IA"""
        try:
            # Validar pregunta
            if not ValidationService.is_valid_question(pregunta):
                return ChatService._handle_invalid_question(sesion, pregunta)
            
            # Obtener términos excluidos
            terminos_excluidos = list(
                TerminoExcluido.objects.filter(usuario=user).values_list("palabra", flat=True)
            )
            
            # Obtener historial
            mensajes = MensajeChat.objects.filter(sesion=sesion).order_by('fecha')
            historial = [
                {"role": "user" if m.tipo_emisor == "usuario" else "assistant", "content": m.contenido}
                for m in mensajes
            ]
            
            # Generar SQL y respuesta
            sql_query = AIService.generate_sql_query(pregunta, historial, terminos_excluidos)
            
            if not ValidationService.is_valid_sql(sql_query):
                return ChatService._handle_invalid_sql(sesion)
            
            # Ejecutar consulta
            filas = ChatService._execute_sql_query(sql_query)
            
            # Generar respuesta final
            respuesta, tipo_relacionado, ids_relacionados = AIService.generate_final_response(
                pregunta, filas, historial
            )
            
            # Procesar y guardar respuesta
            return ChatService._save_response(
                sesion, respuesta, filas, tipo_relacionado, ids_relacionados
            )
            
        except Exception as e:
            logging.error(f"Error processing message: {e}")
            raise
    
    @staticmethod
    def _handle_invalid_question(sesion, pregunta):
        """Maneja preguntas inválidas"""
        advertencia = "⚠️ Tu pregunta no está relacionada con recursos humanos universitarios."
        MensajeChat.objects.create(
            sesion=sesion,
            tipo_emisor="ia",
            contenido=advertencia,
            fecha=timezone.now()
        )
        
        _, razon = ValidationService.is_valid_question(pregunta)
        PreguntaBloqueada.objects.create(
            sesion=sesion,
            pregunta=pregunta,
            razon=razon,
            fecha=timezone.now()
        )
        return {"success": False, "message": advertencia}
    
    @staticmethod
    def _handle_invalid_sql(sesion):
        """Maneja SQL inválido"""
        advertencia = "⚠️ Se detectó una combinación de palabras incoherentes. Intenta reformular la pregunta."
        MensajeChat.objects.create(
            sesion=sesion,
            tipo_emisor="ia",
            contenido=advertencia,
            fecha=timezone.now()
        )
        return {"success": False, "message": advertencia}
    
    @staticmethod
    def _execute_sql_query(sql_query):
        """Ejecuta la consulta SQL y retorna los resultados"""
        with connection.cursor() as cur:
            cur.execute(sql_query)
            columnas = [desc[0] for desc in cur.description]
            filas = [dict(zip(columnas, row)) for row in cur.fetchall()]
        return filas
    
    @staticmethod
    def _save_response(sesion, respuesta, filas, tipo_relacionado, ids_relacionados):
        """Guarda la respuesta y metadatos asociados"""
        # Buscar JSON en la respuesta
        match = re.search(r"\{.*?\}", respuesta)
        ids_extra = None
        if match:
            try:
                ids_extra = json.loads(match.group())
            except json.JSONDecodeError:
                pass
        
        # Crear mensaje
        mensaje = MensajeChat.objects.create(
            sesion=sesion,
            tipo_emisor="ia",
            contenido=respuesta,
            fecha=timezone.now()
        )
        
        # Guardar metadata
        metadata = {}
        if ids_relacionados:
            metadata["tipo"] = tipo_relacionado
            metadata["ids"] = ids_relacionados
        
        if metadata:
            mensaje.metadata = metadata
            mensaje.save()
        
        # Guardar datos fuente
        if filas:
            json_valido = json.dumps(filas)
            DatosFuenteMensaje.objects.create(mensaje=mensaje, datos=json_valido)
        
        return {
            "success": True,
            "message": respuesta,
            "datos_fuente": filas,
            "ids_extra": ids_extra
        }
    
    @staticmethod
    def finalize_session(sesion_id, user_id):
        """Finaliza una sesión de chat"""
        try:
            with connection.cursor() as cur:
                cur.execute(
                    "UPDATE sesion_chat SET estado = 'finalizada', fecha_termino = NOW() WHERE id_sesion = %s AND usuario_id = %s",
                    [sesion_id, user_id]
                )
            return True
        except Exception as e:
            logging.error(f"Error finalizing session: {e}")
            return False
    
    @staticmethod
    def can_delete_session(sesion_id):
        """Verifica si una sesión puede ser eliminada"""
        return not PreguntaBloqueada.objects.filter(sesion_id=sesion_id).exists()
    
    @staticmethod
    def delete_session(sesion_id, user):
        """Elimina una sesión si es posible"""
        if not ChatService.can_delete_session(sesion_id):
            return False
        
        try:
            MensajeChat.objects.filter(sesion_id=sesion_id).delete()
            SesionChat.objects.filter(id_sesion=sesion_id, usuario=user).delete()
            return True
        except Exception as e:
            logging.error(f"Error deleting session: {e}")
            return False