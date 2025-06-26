import psycopg2
import psycopg2.extras
import anthropic
from datetime import datetime
import logging
import re, json
from dotenv import load_dotenv
import os
from chatbot.models import ContextoPrompt

# Configurar logging
logging.basicConfig(
    filename="chatbot_ia.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

# Configuración de la conexión a MariaDB
db_config = {
    "host": "localhost",
    "user": "FelipeAE",
    "password": "Pipe1996",
    "dbname": "test",
    "port": 5432
}

def conectar_db():
    """Crea y devuelve una conexión a la base de datos PostgreSQL."""
    return psycopg2.connect(**db_config)


# ------------------- Configuración de Anthropic -------------------

# Inicializamos el cliente de Anthropic con la clave correspondiente
load_dotenv()
client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))


# Estructura de tablas (adaptar al dataset real)
ESTRUCTURA_TABLA = """
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

# ------------------- FUNCIONES DE BASE DE DATOS -------------------

def crear_sesion(usuario_id=None):
    """Crea una nueva sesión y la almacena en la tabla sesion_chat."""
    conn = conectar_db()
    cur = conn.cursor()
    if usuario_id:
        cur.execute(
            "INSERT INTO sesion_chat (fecha_inicio, estado, nombre_sesion, usuario_id) VALUES (NOW(), 'activa', %s, %s) RETURNING id_sesion",
            ["Sesión de terminal", usuario_id]
        )
    else:
        # Para compatibilidad con versión anterior (sin usuario)
        cur.execute("INSERT INTO sesion_chat (fecha_inicio, estado, nombre_sesion) VALUES (NOW(), 'activa', %s) RETURNING id_sesion", ["Sesión de terminal"])
    id_sesion = cur.fetchone()[0]
    conn.commit()
    cur.close()
    conn.close()
    logging.info(f"Sesión creada: ID {id_sesion}")
    return id_sesion

def finalizar_sesion(id_sesion):
    """Marca la sesión como finalizada."""
    conn = conectar_db()
    cur = conn.cursor()
    cur.execute(
        "UPDATE sesion_chat SET fecha_termino = NOW(), estado = 'finalizada' WHERE id_sesion = %s",
        (id_sesion,)
    )
    conn.commit()
    cur.close()
    conn.close()
    logging.info(f"Sesión {id_sesion} finalizada.")

def guardar_mensaje(id_sesion, tipo_emisor, contenido):
    """
    Guarda un mensaje (usuario o IA) en la tabla mensaje_chat.
    Usa la columna 'contenido' (no 'mensaje'), tal como en el script original. :contentReference[oaicite:1]{index=1}
    """
    conn = conectar_db()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO mensaje_chat (id_sesion, tipo_emisor, contenido) VALUES (%s, %s, %s)",
        (id_sesion, tipo_emisor, contenido)
    )

    # Si es el primer mensaje del usuario, lo usamos como nombre de sesión
    if tipo_emisor == "usuario":
        cur.execute(
            "SELECT COUNT(*) FROM mensaje_chat WHERE id_sesion = %s AND tipo_emisor = 'usuario'",
            (id_sesion,)
        )
        count = cur.fetchone()[0]
        if count == 1:
            resumen = contenido.strip()[:80]  # Nombre corto (primeros 80 caracteres)
            cur.execute(
                "UPDATE sesion_chat SET nombre_sesion = %s WHERE id_sesion = %s",
                (resumen, id_sesion)
            )
            logging.info(f"Nombre de sesión {id_sesion} actualizado: {resumen}")

    conn.commit()
    cur.close()
    conn.close()

def obtener_historial(id_sesion):
    """
    Recupera el historial de mensajes de una sesión en orden cronológico,
    retornándolo como una lista de diccionarios con keys 'role' y 'content',
    usando 'contenido' en lugar de 'mensaje'. :contentReference[oaicite:2]{index=2}
    """
    conn = conectar_db()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cur.execute(
        "SELECT tipo_emisor, contenido FROM mensaje_chat WHERE id_sesion = %s ORDER BY fecha ASC",
        (id_sesion,)
    )
    filas = cur.fetchall()
    cur.close()
    conn.close()
    # Convertir cada fila a {"role": "...", "content": "..."}
    mensajes = []
    for m in filas:
        role = "user" if m["tipo_emisor"] == "usuario" else "assistant"
        mensajes.append({"role": role, "content": m["contenido"]})
    return mensajes

def ejecutar_sql(query):
    """Ejecuta una consulta SQL de solo lectura (SELECT) y devuelve los resultados."""
    conn = conectar_db()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cur.execute(query)
    resultados = cur.fetchall()
    cur.close()
    conn.close()
    return resultados

# ------------------- GESTIÓN DE PREGUNTAS BLOQUEADAS -------------------

def es_pregunta_valida(pregunta):
    """
    Valida semánticamente que la pregunta esté relacionada con el dominio de recursos humanos.
    Devuelve (True, None) si es válida o (False, razón) si no lo es.
    """
    pregunta_lower = pregunta.lower().strip()

    absurdos = [
        "galaxia", "alien", "extraterrestre", "quien gano el mundial de quidditch",
        "cocinar", "pastel de papas", "inflacion en saturno", "marciano", "dragones"
    ]
    if any(p in pregunta_lower for p in absurdos):
        return False, "Pregunta absurda o fuera de contexto"

    claves_validas = [
        "honorario", "contrato", "persona", "nombre", "apellido", "funcion", "calificacion",
        "región", "mes", "año", "pagado", "liquido", "bruto", "tipo de pago", "profesion",
        "psicólogo", "sueldo", "remuneración", "trabajador", "gasto", "top", "más ganaron", "ganó"
    ]
    if any(p in pregunta_lower for p in claves_validas):
        return True, None

    if len(pregunta_lower.split()) >= 4 and re.search(r"(cu[aá]nto|cu[aá]les|d[aá]me|muestra|qu[ée]|qu[íi]en)", pregunta_lower):
        return True, None

    return False, "No contiene términos relacionados ni estructura válida"

def registrar_pregunta_bloqueada(id_sesion, pregunta, razon):
    """Inserta en la tabla preguntas_bloqueadas las preguntas no válidas."""
    conn = conectar_db()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO preguntas_bloqueadas (id_sesion, pregunta, razon) VALUES (%s, %s, %s)",
        (id_sesion, pregunta, razon)
    )
    conn.commit()
    cur.close()
    conn.close()
    logging.warning(f"Pregunta bloqueada registrada: {pregunta} - Razón: {razon}")

def hay_preguntas_bloqueadas_en_sesion(id_sesion):
    """
    Retorna True si existe al menos una pregunta bloqueada asociada a la sesión dada.
    """
    conn = conectar_db()
    cur = conn.cursor()
    cur.execute(
        "SELECT COUNT(*) FROM preguntas_bloqueadas WHERE id_sesion = %s",
        (id_sesion,)
    )
    count = cur.fetchone()[0]
    cur.close()
    conn.close()
    return count > 0

def eliminar_sesion_si_valida(id_borrar):
    """
    Verifica si la sesión tiene preguntas bloqueadas.
    - Si sí las tiene, muestra mensaje y no borra.
    - Si no tiene, borra mensajes y metadatos de la sesión.
    """
    if hay_preguntas_bloqueadas_en_sesion(id_borrar):
        print("❌ No se puede eliminar: la sesión contiene preguntas bloqueadas que deben conservarse como evidencia.")
        return

    conn = conectar_db()
    cur = conn.cursor()
    cur.execute("DELETE FROM mensaje_chat WHERE id_sesion = %s", (id_borrar,))
    cur.execute("DELETE FROM sesion_chat WHERE id_sesion = %s", (id_borrar,))
    conn.commit()
    cur.close()
    conn.close()
    print(f"✅ Sesión {id_borrar} eliminada correctamente.")
    logging.info(f"Sesión {id_borrar} eliminada.")

# ------------------- GENERACIÓN DE CONSULTA SQL (ANTHROPIC) -------------------

def obtener_consulta_sql(pregunta, historial, terminos_excluidos=None):
    contexto = ContextoPrompt.objects.filter(activo=True).first()
    prompt_base = contexto.prompt_sistema if contexto else "Eres un asistente experto en análisis de datos para RRHH universitarios. Responde preguntas basadas en las siguientes tablas relacionales:\n" + ESTRUCTURA_TABLA
    """
    Utiliza Anthropic (Claude) para generar la consulta SQL en base a la pregunta del usuario
    y el historial de mensajes de la sesión.
    """
    
    # Agregar información sobre términos excluidos si existen
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
11. Si el usuario pregunta por “los anteriores” o “las personas anteriores”, asume que se refiere al resultado más reciente de la conversación, y genera una consulta coherente filtrando por los mismos nombres si es posible.
12. Si no puedes generar una consulta válida o la pregunta no se relaciona con el contexto de los datos, responde amablemente que no puedes responder a esa consulta.
13. OBLIGATORIO: Si hay términos excluidos configurados (mostrados arriba), debes aplicar TODOS los filtros de exclusión correspondientes usando condiciones WHERE con NOT LIKE.


Tu respuesta debe ser solo la consulta SQL, sin explicaciones adicionales.
"""

    response = client.messages.create(
        model="claude-3-5-haiku-latest",
        max_tokens=1000,
        temperature=0,
        messages=[{"role": "user", "content": system_prompt}] + historial
    )

    return response.content[0].text.strip()

# ------------------- GENERACIÓN DE RESPUESTA FINAL (ANTHROPIC) -------------------

def generar_respuesta_final(pregunta, resultado_sql, historial):
    """
    Utiliza Anthropic (Claude) para generar la respuesta de usuario final en lenguaje natural,
    a partir de la pregunta original y los resultados obtenidos de la consulta SQL.
    
    """
    prompt = f"""Dada la siguiente pregunta:
\"{pregunta}\"
Y los siguientes resultados:
{resultado_sql}

Genera una respuesta clara para un usuario de RRHH universitario. Sigue estas pautas:
- Usa lenguaje profesional y ordenado.
- Muestra cifras con formato de pesos chilenos ($ 1.000.000).
- Si hay varios datos personales o contratos, incluye un JSON al final así: {{"id_contrato": [12, 15, 18]}} o {{"id_persona": [5, 7, 9]}}.
- Esa instrucción no debe ser explicada, solo insertada al final como dato estructurado, la instruccion que esta puesta arriba es solo un ejemplo no tomes ese dato para dar informacion, tienes que buscar el dato especifico de la informacion que se te pide o de la persona como tal o contrato de donde extrajiste la informacion.
- Si no hay datos, indica que no se encontró información y sugiere reformular la pregunta.
"""

    response = client.messages.create(
        model="claude-3-5-haiku-latest",
        max_tokens=1000,
        temperature=0,
        messages=[{"role": "user", "content": prompt}] + historial
    )

    texto = response.content[0].text.strip()

    # Buscar JSON al final del texto
    patron_json = r'(\{.*\})\s*$'  # Busca algo tipo {...} al final
    coincidencia = re.search(patron_json, texto)

    ids = []
    tipo = None

    if coincidencia:
        try:
            json_str = coincidencia.group(1)
            data = json.loads(json_str)
            # Ej: {'id_persona': [5, 7, 9]} → tipo: persona, ids: [5, 7, 9]
            for clave, valores in data.items():
                if clave.startswith("id_") and isinstance(valores, list):
                    tipo = clave  # 'id_persona'
                    ids = valores
                    # Remueve el JSON del final del texto limpio
                    texto = texto[:coincidencia.start()].strip()
                    break
        except json.JSONDecodeError:
            pass  # Si falla el parseo, ignora

    return texto, tipo, ids

# ------------------- VISUALIZACIÓN DE SESIONES -------------------

def mostrar_sesiones():
    """
    Muestra todas las sesiones registradas. Si una sesión tiene preguntas bloqueadas,
    muestra una advertencia junto a su descripción.
    """
    conn = conectar_db()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cur.execute(
        "SELECT id_sesion, nombre_sesion, fecha_inicio, estado FROM sesion_chat ORDER BY fecha_inicio DESC"
    )
    sesiones = cur.fetchall()
    cur.close()
    conn.close()

    if not sesiones:
        print("📂 No hay sesiones registradas.")
        return None

    print("📂 Sesiones disponibles:")
    for sesion in sesiones:
        ses_id = sesion['id_sesion']
        estado = "🟢 Activa" if sesion['estado'] == 'activa' else "⚪ Finalizada"
        nombre = sesion['nombre_sesion'] or "Sin nombre"
        advertencia = " ⚠️ Contiene preguntas bloqueadas" if hay_preguntas_bloqueadas_en_sesion(ses_id) else ""
        print(f"{estado} - ID {ses_id} – {nombre} – {sesion['fecha_inicio']}{advertencia}")

    return sesiones

# ------------------- BUCLE PRINCIPAL -------------------

def main():
    print("🧠 Chatbot RRHH – Evaluación 2 IA")

    # Menú inicial: elegir sesión o crear nueva
    while True:
        print("\n🧠 ¿Qué deseas hacer?")
        print("1. Ver sesiones")
        print("2. Iniciar nueva conversación")
        print("3. Salir")
        opcion = input("Elige una opción (1/2/3): ").strip()

        if opcion == "1":
            sesiones = mostrar_sesiones()
            if sesiones:
                try:
                    id_elegido = int(input("🔍 Ingresa el ID de la sesión a retomar o solo leer: "))
                    estado = next((s['estado'] for s in sesiones if s['id_sesion'] == id_elegido), None)
                    if estado == 'activa':
                        id_sesion = id_elegido
                        solo_lectura = False
                        print(f"🔄 Sesión {id_sesion} retomada (activa).")
                    elif estado == 'finalizada':
                        id_sesion = id_elegido
                        solo_lectura = True
                        print(f"📖 Sesión {id_sesion} abierta en modo solo lectura.\n")
                        # Mostrar todo el historial en modo lectura
                        historial_completo = obtener_historial(id_sesion)
                        for msg in historial_completo:
                            rol_icono = "👤" if msg["role"] == "user" else "🤖"
                            print(f"{rol_icono} {msg['content']}")
                        print("\n📖 Fin del historial. No puedes agregar más mensajes a esta sesión.")
                    else:
                        print("⚠️ ID no válido.")
                        continue
                    break
                except ValueError:
                    print("⚠️ Ingresa un número válido.")
                except StopIteration:
                    print("⚠️ Sesión no encontrada.")
                except Exception as e:
                    print(f"⚠️ Error: {e}")
            continue

        elif opcion == "2":
            id_sesion = crear_sesion()
            solo_lectura = False
            print(f"🆕 Nueva sesión iniciada. ID: {id_sesion}")
            break

        elif opcion == "3":
            print("👋 ¡Hasta luego!")
            return

        else:
            print("⚠️ Opción no válida. Elige 1, 2 o 3.")

    # ------------------------- FASE DE CHAT -------------------------

    historial = obtener_historial(id_sesion)

    while True:
        print("\n💡 Comandos disponibles: salir | nuevo | sesiones | borrar {id}")
        if solo_lectura:
            print("📖 Esta sesión está finalizada – solo puedes ver la conversación.")
        pregunta = input("👤 Tú: ")

        if pregunta.strip().lower() == "salir":
            if not solo_lectura:
                finalizar_sesion(id_sesion)
                print("🛑 Sesión finalizada.")
            break

        elif pregunta.strip().lower() == "nuevo":
            if not solo_lectura:
                finalizar_sesion(id_sesion)
            id_sesion = crear_sesion()
            historial = []
            solo_lectura = False
            print(f"🆕 Nueva sesión iniciada. ID: {id_sesion}")
            continue

        elif pregunta.strip().lower() == "sesiones":
            mostrar_sesiones()
            continue

        elif pregunta.lower().startswith("borrar "):
            try:
                id_borrar = int(pregunta.strip().split()[1])
                eliminar_sesion_si_valida(id_borrar)
            except ValueError:
                print("⚠️ El ID debe ser un número entero.")
            except Exception as e:
                print(f"⚠️ Error al intentar borrar la sesión: {e}")
            continue

        elif not pregunta.strip():
            print("⚠️ Ingresa una pregunta válida.")
            continue

        # Si la sesión está en modo solo lectura, no dejamos procesar preguntas nuevas
        if solo_lectura:
            print("⚠️ No puedes hacer preguntas en una sesión finalizada.")
            continue

        # ----------------- Procesamiento de la pregunta -----------------

        try:
            # Guardamos el mensaje del usuario
            guardar_mensaje(id_sesion, "usuario", pregunta)

            # Validar semánticamente la pregunta antes de procesarla
            es_valida, razon = es_pregunta_valida(pregunta)
            if not es_valida:
                advertencia = "⚠️ Tu pregunta no está relacionada con los datos de recursos humanos universitarios."
                print(advertencia)
                guardar_mensaje(id_sesion, "ia", advertencia)
                registrar_pregunta_bloqueada(id_sesion, pregunta, razon)
                continue

            # Obtenemos de nuevo el historial actualizado
            historial = obtener_historial(id_sesion)

            # Generar consulta SQL usando la función original
            sql_query = obtener_consulta_sql(pregunta, historial)
            logging.info(f"SQL generado: {sql_query}")
            # Validación contra SELECT DISTINCT + ORDER BY CASE que puede fallar en PostgreSQL
            sql_flat = sql_query.replace("\n", " ").lower()
            if "select distinct" in sql_flat and "order by" in sql_flat and "case" in sql_flat:
                advertencia = "⚠️ Se detectó una combinación de palabras incoherentes. Intenta reformular la pregunta."
                print(advertencia)
                guardar_mensaje(id_sesion, "ia", advertencia)
                continue


            if not sql_query.lower().strip().startswith("select"):
                logging.warning("Claude no generó una consulta SQL válida.")
                advertencia = "⚠️ Se detectó una combinación de palabras incoherentes. Intenta reformular la pregunta."
                print(advertencia)
                guardar_mensaje(id_sesion, "ia", advertencia)
                continue

            # Ejecutamos la consulta y obtenemos resultados
            resultados = ejecutar_sql(sql_query)

            # Generar respuesta final en lenguaje natural usando la función original
            respuesta = generar_respuesta_final(pregunta, resultados, historial)

            guardar_mensaje(id_sesion, "ia", respuesta)
            print(f"🤖 IA: {respuesta}")

        except Exception as e:
            print(f"❌ Error: {e}")
            logging.error(f"Error al procesar: {str(e)}")

if __name__ == "__main__":
    main()
