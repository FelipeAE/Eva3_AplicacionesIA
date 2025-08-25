# Chatbot RRHH - API Documentation

## Base URL
```
http://localhost:8000/api/v1/
```

## Authentication
Todas las APIs requieren autenticación de Django. El usuario debe estar logueado.
Para APIs de admin se requiere `is_staff = True`.

---

## 📱 Chat APIs

### GET `/sessions/`
Lista las sesiones del usuario actual.

**Query Parameters:**
- `page` (opcional): Número de página (default: 1)
- `per_page` (opcional): Items por página (default: 10)

**Response:**
```json
{
  "sessions": [
    {
      "id": 1,
      "name": "Mi conversación",
      "status": "activa",
      "created_at": "2024-01-01T10:00:00Z",
      "finished_at": null
    }
  ],
  "pagination": {
    "current_page": 1,
    "total_pages": 2,
    "has_next": true,
    "has_previous": false,
    "total_count": 15
  }
}
```

### POST `/sessions/create/`
Crea una nueva sesión de chat.

**Response:**
```json
{
  "success": true,
  "session_id": 123,
  "message": "Sesión creada exitosamente"
}
```

### GET `/sessions/{session_id}/`
Obtiene detalles de una sesión específica y todos sus mensajes.

**Response:**
```json
{
  "session": {
    "id": 123,
    "name": "Mi conversación",
    "status": "activa",
    "created_at": "2024-01-01T10:00:00Z",
    "finished_at": null,
    "readonly": false,
    "has_blocked_questions": false
  },
  "messages": [
    {
      "id": 1,
      "sender": "usuario",
      "content": "Dame el top 5 de honorarios",
      "timestamp": "2024-01-01T10:01:00Z",
      "has_source_data": false
    },
    {
      "id": 2,
      "sender": "ia",
      "content": "Aquí están los top 5 honorarios...",
      "timestamp": "2024-01-01T10:01:30Z",
      "has_source_data": true
    }
  ],
  "context": {
    "active_context": "Juan Mir"
  }
}
```

### POST `/sessions/{session_id}/message/`
Envía un mensaje a la sesión de chat.

**Request Body:**
```json
{
  "message": "Dame el top 5 de honorarios de marzo"
}
```

**Response:**
```json
{
  "success": true,
  "message": "Mensaje procesado exitosamente",
  "response": "Aquí están los top 5 honorarios de marzo... ES INCREIBLE!",
  "has_source_data": true,
  "metadata": {"id_contrato": [12, 15, 18]}
}
```

### POST `/sessions/{session_id}/finalize/`
Finaliza una sesión (la pone en solo lectura).

**Response:**
```json
{
  "success": true,
  "message": "Sesión finalizada exitosamente"
}
```

### DELETE `/sessions/{session_id}/delete/`
Elimina una sesión (solo si no tiene preguntas bloqueadas).

**Response:**
```json
{
  "success": true,
  "message": "Sesión eliminada exitosamente"
}
```

---

## 🔧 Admin APIs (Staff Only)

### GET `/admin/contexts/`
Lista todos los contextos de prompt disponibles.

**Response:**
```json
{
  "contexts": [
    {
      "id": 1,
      "name": "Juan Mir",
      "active": true,
      "prompt": "Cada vez que vayas a responder una pregunta termina la frase con ES INCREIBLE!"
    }
  ]
}
```

### POST `/admin/contexts/create/`
Crea un nuevo contexto de prompt.

**Request Body:**
```json
{
  "name": "Contexto Formal",
  "prompt": "Responde de manera muy formal y profesional"
}
```

**Response:**
```json
{
  "success": true,
  "message": "Contexto creado exitosamente",
  "context": {
    "id": 2,
    "name": "Contexto Formal",
    "active": false
  }
}
```

### POST `/admin/contexts/{context_id}/activate/`
Activa un contexto específico (desactiva todos los demás).

**Response:**
```json
{
  "success": true,
  "message": "Contexto 'Juan Mir' activado exitosamente"
}
```

### POST `/admin/contexts/{context_id}/deactivate/`
Desactiva un contexto específico.

**Response:**
```json
{
  "success": true,
  "message": "Contexto 'Juan Mir' desactivado exitosamente"
}
```

### DELETE `/admin/contexts/{context_id}/delete/`
Elimina un contexto permanentemente.

**Response:**
```json
{
  "success": true,
  "message": "Contexto 'Juan Mir' eliminado exitosamente"
}
```

---

## ⚙️ User Settings APIs

### GET `/settings/excluded-terms/`
Lista los términos que el usuario ha excluido de las búsquedas.

**Response:**
```json
{
  "excluded_terms": [
    {
      "id": 1,
      "term": "marzo"
    },
    {
      "id": 2,
      "term": "psicólogo"
    }
  ]
}
```

### POST `/settings/excluded-terms/add/`
Agrega un nuevo término excluido.

**Request Body:**
```json
{
  "term": "santiago"
}
```

**Response:**
```json
{
  "success": true,
  "message": "Término 'santiago' agregado exitosamente"
}
```

### DELETE `/settings/excluded-terms/{term_id}/delete/`
Elimina un término de la lista de exclusiones.

**Response:**
```json
{
  "success": true,
  "message": "Término 'santiago' eliminado exitosamente"
}
```

---

## 📊 Data APIs (Legacy)

### GET `/contrato/{id}/`
Obtiene detalles de un contrato específico.

**Response:**
```json
{
  "id": 123,
  "honorario_total_bruto": 1500000,
  "tipo_pago": "Mensual",
  "viaticos": "No",
  "observaciones": "...",
  "enlace_funciones": "...",
  "persona": "GONZÁLEZ, MARÍA",
  "funcion": "Psicólogo/a",
  "calificacion": "Profesional",
  "mes": "marzo",
  "anho": 2024,
  "region": "Metropolitana"
}
```

### GET `/detalle/{tipo}/{id}/`
Obtiene detalles genéricos de una entidad (persona, funcion, tiempo, contrato).

**Response:**
```json
{
  "id_persona": 1,
  "nombre_completo": "GONZÁLEZ, MARÍA",
  // ... otros campos según el tipo
}
```

---

## Error Responses

Todas las APIs pueden retornar estos tipos de error:

### 400 Bad Request
```json
{
  "success": false,
  "error": "El mensaje no puede estar vacío"
}
```

### 401 Unauthorized
```json
{
  "error": "Authentication required"
}
```

### 403 Forbidden
```json
{
  "error": "Staff permissions required"
}
```

### 404 Not Found
```json
{
  "error": "Sesión no encontrada"
}
```

### 500 Internal Server Error
```json
{
  "success": false,
  "error": "Error interno del servidor"
}
```

---

## Example Usage with JavaScript

```javascript
// Crear nueva sesión
const response = await fetch('/api/v1/sessions/create/', {
  method: 'POST',
  headers: {
    'X-CSRFToken': getCookie('csrftoken'),
    'Content-Type': 'application/json',
  }
});
const data = await response.json();
console.log('Nueva sesión:', data.session_id);

// Enviar mensaje
const messageResponse = await fetch(`/api/v1/sessions/${sessionId}/message/`, {
  method: 'POST',
  headers: {
    'X-CSRFToken': getCookie('csrftoken'),
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({
    message: 'Dame el top 5 de honorarios'
  })
});
const messageData = await messageResponse.json();
console.log('Respuesta del bot:', messageData.response);
```

---

## Status
✅ APIs implementadas y listas para usar
✅ Documentación completa
✅ Compatible con la funcionalidad web existente
✅ Preparado para frontend React o cualquier SPA