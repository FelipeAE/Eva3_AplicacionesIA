import json
import re
import logging
import anthropic
import os
from dotenv import load_dotenv

from ..models import ContextoPrompt

# Cargar variables de entorno
load_dotenv()

class AIService:
    """Servicio para interacciones con la API de Anthropic Claude"""
    
    def __init__(self):
        self.client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
        self.estructura_tabla = self._get_table_structure()
    
    @staticmethod
    def _get_table_structure():
        """Retorna la estructura de tablas de la base de datos"""
        return """
TABLA persona
  id_persona SERIAL,
  nombre_completo TEXT

TABLA funcion
  id_funcion SERIAL,
  grado_eus INT,
  descripcion_funcion TEXT,
  calificacion_profesional TEXT

TABLA tiempo_contrato
  id_tiempo SERIAL,
  anho INT,
  mes TEXT,
  fecha_inicio DATE,
  fecha_termino DATE,
  region TEXT

TABLA contrato
  id_contrato SERIAL,
  id_persona INT,
  id_funcion INT,
  id_tiempo INT,
  honorario_total_bruto INT,
  tipo_pago TEXT,
  viaticos TEXT,
  observaciones TEXT,
  enlace_funciones TEXT

Relaciones:
- contrato.id_persona → persona.id_persona
- contrato.id_funcion → funcion.id_funcion
- contrato.id_tiempo → tiempo_contrato.id_tiempo
"""
    
    @staticmethod
    def generate_sql_query(pregunta, historial, terminos_excluidos=None):
        """Genera una consulta SQL basada en la pregunta del usuario"""
        try:
            ai_service = AIService()
            
            # Para SQL siempre usamos el prompt estándar, NO el contexto personalizado
            prompt_base = f"Eres un asistente experto en análisis de datos para RRHH universitarios. Responde preguntas basadas en las siguientes tablas relacionales:\n{ai_service.estructura_tabla}"
            logging.info("USANDO PROMPT ESTÁNDAR PARA SQL - SIN CONTEXTO PERSONALIZADO")
            
            # Agregar información sobre términos excluidos
            exclusiones_info = ""
            if terminos_excluidos:
                exclusiones_info = f"""

IMPORTANTE - TÉRMINOS EXCLUIDOS: El usuario ha configurado los siguientes términos para EXCLUIR completamente de los resultados: {', '.join(terminos_excluidos)}.

Debes agregar condiciones WHERE para filtrar estos términos en TODAS las columnas relevantes:
- Si un término coincide con un mes (enero, febrero, marzo, etc.), agrega: AND LOWER(tiempo_contrato.mes) NOT LIKE '%término%'
- Si un término coincide con una región, agrega: AND LOWER(tiempo_contrato.region) NOT LIKE '%término%'  
- Si un término coincide con un nombre/apellido, agrega: AND LOWER(persona.nombre_completo) NOT LIKE '%término%'
- Si un término coincide con una función, agrega: AND LOWER(funcion.descripcion_funcion) NOT LIKE '%término%'
- Si un término coincide con una calificación, agrega: AND LOWER(funcion.calificacion_profesional) NOT LIKE '%término%'

Ejemplo: Si 'marzo' está excluido, la consulta debe incluir: AND LOWER(tiempo_contrato.mes) NOT LIKE '%marzo%'
Los filtros de exclusión son OBLIGATORIOS y deben aplicarse siempre que haya términos excluidos."""
            
            system_prompt = f"""{prompt_base}{exclusiones_info}

Y la siguiente consulta en lenguaje natural:
\"{pregunta}\"

Genera una consulta SQL para el motor PostgreSQL que responda la pregunta del usuario. Sigue estas pautas:
1. Usa exclusivamente las tablas y relaciones provistas.
2. Utiliza JOIN cuando sea necesario combinar información entre tablas.
3. Usa LIKE y funciones como LOWER para permitir búsquedas insensibles a mayúsculas.
4. Siempre que busques por nombres, considera que están en formato: "APELLIDOS, NOMBRES".
5. Si el usuario entrega el nombre en formato natural (ej. "Felipe Álvarez"), intenta invertirlo o comparar ambos extremos usando LIKE con comodines.
6. Utiliza funciones agregadas como COUNT, SUM, AVG, MAX o MIN cuando la pregunta lo sugiera.
7. Ordena los resultados cuando sea útil, por ejemplo usando ORDER BY honorario_total_bruto DESC.
8. Limita el resultado a 100 filas como máximo. Usa LIMIT 100.
9. Nunca generes comandos como CREATE, DROP, INSERT ni UPDATE. Solo SELECT.
10. Usa alias de tabla cuando sea necesario para mantener claridad.
11. Si el usuario pregunta por "los anteriores" o "las personas anteriores", asume que se refiere al resultado más reciente de la conversación, y genera una consulta coherente filtrando por los mismos nombres si es posible.
12. Si no puedes generar una consulta válida o la pregunta no se relaciona con el contexto de los datos, responde amablemente que no puedes responder a esa consulta.
13. OBLIGATORIO: Si hay términos excluidos configurados (mostrados arriba), debes aplicar TODOS los filtros de exclusión correspondientes usando condiciones WHERE con NOT LIKE.
14. MUY IMPORTANTE: SIEMPRE incluye los campos de ID relevantes (id_contrato, id_persona, id_funcion, id_tiempo) en el SELECT para permitir referencias posteriores. Por ejemplo, si consultas datos de contratos, SIEMPRE incluye c.id_contrato en el SELECT.

Tu respuesta debe ser solo la consulta SQL, sin explicaciones adicionales.
"""
            
            response = ai_service.client.messages.create(
                model="claude-3-5-haiku-latest",
                max_tokens=1000,
                temperature=0,
                messages=[{"role": "user", "content": system_prompt}] + historial
            )
            
            sql_query = response.content[0].text.strip()
            
            # Limpiar el SQL de comentarios extras y texto no SQL
            sql_limpio = ai_service._clean_sql(sql_query)
            logging.info(f"SQL original: {sql_query}")
            logging.info(f"SQL limpio: {sql_limpio}")
            
            return sql_limpio
            
        except Exception as e:
            logging.error(f"Error generando consulta SQL: {e}")
            raise
    
    @staticmethod
    def generate_final_response(pregunta, resultado_sql, historial):
        """Genera la respuesta final en lenguaje natural"""
        try:
            ai_service = AIService()
            
            # Obtener contexto personalizado si existe
            contexto = ContextoPrompt.objects.filter(activo=True).first()
            contexto_personalizado = ""
            if contexto:
                contexto_personalizado = f"\n\nINSTRUCCIÓN ESPECIAL DEL USUARIO: {contexto.prompt_sistema}"
            
            prompt = f"""Dada la siguiente pregunta:
\"{pregunta}\"
Y los siguientes resultados:
{resultado_sql}

Genera una respuesta clara para un usuario de RRHH universitario. Sigue estas pautas:
- Usa lenguaje profesional y ordenado.
- Muestra cifras con formato de pesos chilenos ($ 1.000.000).
- Si hay varios datos personales o contratos, incluye un JSON al final así: {{"id_contrato": [12, 15, 18]}} o {{"id_persona": [5, 7, 9]}}.
- Esa instrucción no debe ser explicada, solo insertada al final como dato estructurado, la instruccion que esta puesta arriba es solo un ejemplo no tomes ese dato para dar informacion, tienes que buscar el dato especifico de la informacion que se te pide o de la persona como tal o contrato de donde extrajiste la informacion.
- Si no hay datos, indica que no se encontró información y sugiere reformular la pregunta.{contexto_personalizado}
"""
            
            response = ai_service.client.messages.create(
                model="claude-3-5-haiku-latest",
                max_tokens=1000,
                temperature=0,
                messages=[{"role": "user", "content": prompt}] + historial
            )
            
            texto = response.content[0].text.strip()
            
            # Extraer JSON y metadatos
            return ai_service._extract_metadata_from_response(texto)
            
        except Exception as e:
            logging.error(f"Error generando respuesta final: {e}")
            raise
    
    @staticmethod
    def _extract_metadata_from_response(texto):
        """Extrae metadatos JSON de la respuesta de la IA"""
        # Buscar JSON al final del texto
        patron_json = r'(\{.*\})\s*$'
        coincidencia = re.search(patron_json, texto)
        
        ids = []
        tipo = None
        
        if coincidencia:
            try:
                json_str = coincidencia.group(1)
                data = json.loads(json_str)
                
                for clave, valores in data.items():
                    if clave.startswith("id_") and isinstance(valores, list):
                        tipo = clave
                        ids = valores
                        # Remover el JSON del texto
                        texto = texto[:coincidencia.start()].strip()
                        break
                        
            except json.JSONDecodeError:
                logging.warning("Error parseando JSON en respuesta de IA")
        
        return texto, tipo, ids
    
    @staticmethod
    def _clean_sql(sql_raw):
        """
        Limpia el SQL generado por la IA eliminando comentarios y texto extra.
        Solo mantiene la consulta SQL válida.
        """
        import re
        
        # Remover comentarios de línea (-- comentario)
        lineas = sql_raw.split('\n')
        lineas_limpias = []
        
        for linea in lineas:
            # Encontrar posición del comentario de línea
            pos_comentario = linea.find('--')
            if pos_comentario != -1:
                linea = linea[:pos_comentario]
            lineas_limpias.append(linea.strip())
        
        sql_sin_comentarios = ' '.join(lineas_limpias).strip()
        
        # Buscar la primera aparición de SELECT y tomar solo hasta el punto y coma o final
        inicio_select = sql_sin_comentarios.upper().find('SELECT')
        if inicio_select == -1:
            return sql_sin_comentarios
        
        sql_desde_select = sql_sin_comentarios[inicio_select:]
        
        # Encontrar el final de la consulta (punto y coma o palabras clave no-SQL)
        palabras_no_sql = ['ES INCREIBLE', '¡', 'EXCELENTE', 'PERFECTO', 'GENIAL', 'INCREÍBLE', 'MARAVILLOSO', 'FANTÁSTICO']
        
        sql_final = sql_desde_select
        for palabra in palabras_no_sql:
            pos = sql_final.upper().find(palabra)
            if pos != -1:
                sql_final = sql_final[:pos].strip()
        
        # También limpiar cualquier texto después de LIMIT si contiene no-números
        # Buscar LIMIT seguido de número y después texto
        match = re.search(r'(LIMIT\s+\d+)\s+[A-Z]', sql_final, re.IGNORECASE)
        if match:
            sql_final = sql_final[:match.start() + len(match.group(1))]
        
        # Asegurar que termina con punto y coma
        if not sql_final.endswith(';'):
            sql_final += ';'
            
        return sql_final