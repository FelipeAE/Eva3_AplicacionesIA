import re


class ValidationService:
    """Servicio para validaciones del sistema"""
    
    @staticmethod
    def is_valid_question(pregunta):
        """
        Valida semánticamente que la pregunta esté relacionada con el dominio de recursos humanos.
        Retorna (True, None) si es válida o (False, razón) si no lo es.
        """
        pregunta_lower = pregunta.lower().strip()

        # Palabras absurdas que definitivamente no son del dominio
        absurdos = [
            "galaxia", "alien", "extraterrestre", "quien gano el mundial de quidditch",
            "cocinar", "pastel de papas", "inflacion en saturno", "marciano", "dragones"
        ]
        if any(p in pregunta_lower for p in absurdos):
            return False, "Pregunta absurda o fuera de contexto"

        # Palabras clave válidas del dominio de RRHH
        claves_validas = [
            "honorario", "contrato", "persona", "nombre", "apellido", "funcion", "calificacion",
            "región", "mes", "año", "pagado", "liquido", "bruto", "tipo de pago", "profesion",
            "psicólogo", "sueldo", "remuneración", "trabajador", "gasto", "top", "más ganaron", "ganó"
        ]
        if any(p in pregunta_lower for p in claves_validas):
            return True, None

        # Verificar estructura de pregunta válida
        if len(pregunta_lower.split()) >= 4 and re.search(
            r"(cu[aá]nto|cu[aá]les|d[aá]me|muestra|qu[ée]|qu[íi]en)", 
            pregunta_lower
        ):
            return True, None

        return False, "No contiene términos relacionados ni estructura válida"
    
    @staticmethod
    def is_valid_sql(sql_query):
        """Valida que la consulta SQL sea válida y segura"""
        if not sql_query:
            return False
        
        sql_lower = sql_query.lower().strip()
        
        # Debe empezar con SELECT
        if not sql_lower.startswith("select"):
            return False
        
        # Verificar combinaciones problemáticas
        sql_flat = sql_query.replace("\n", " ").lower()
        if "select distinct" in sql_flat and "order by" in sql_flat and "case" in sql_flat:
            return False
        
        # Verificar que no contenga comandos peligrosos
        comandos_peligrosos = [
            "drop", "delete", "insert", "update", "alter", "create", 
            "truncate", "exec", "execute", "grant", "revoke"
        ]
        
        for comando in comandos_peligrosos:
            if f" {comando} " in f" {sql_lower} ":
                return False
        
        return True
    
    @staticmethod
    def sanitize_input(input_text):
        """Sanitiza entrada de usuario"""
        if not input_text:
            return ""
        
        # Remover caracteres potencialmente peligrosos
        sanitized = re.sub(r'[<>"\';]', '', str(input_text))
        
        # Limitar longitud
        return sanitized.strip()[:1000]
    
    @staticmethod
    def validate_session_access(sesion, user):
        """Valida que el usuario tenga acceso a la sesión"""
        return sesion.usuario == user
    
    @staticmethod
    def is_session_readonly(sesion):
        """Verifica si la sesión está en modo solo lectura"""
        return sesion.estado == 'finalizada'