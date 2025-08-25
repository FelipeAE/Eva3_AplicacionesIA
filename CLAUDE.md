# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Django-based chatbot application for university human resources (RRHH) data analysis. It integrates Anthropic's Claude AI to generate PostgreSQL queries and provide intelligent responses about HR contracts, personnel, and financial data.

## Development Commands

### Core Django Commands
```bash
# Run development server
python manage.py runserver

# Database migrations
python manage.py makemigrations
python manage.py migrate

# System check (equivalent to linting)
python manage.py check

# Run tests
python manage.py test

# Create superuser
python manage.py createsuperuser
```

### Utility Scripts
```bash
# Add user_id to existing sessions
python agregar_usuario_sesion.py

# Assign orphaned sessions to superuser
python asignar_sesiones_superuser.py

# Test term exclusion functionality
python test_exclusions.py
```

## Architecture Overview

### Database Strategy
The application uses a **mixed database approach**:
- **Unmanaged Models**: HR data (`Persona`, `Funcion`, `TiempoContrato`, `Contrato`) - these point to existing PostgreSQL tables that Django doesn't control
- **Managed Models**: Chatbot functionality (`SesionChat`, `MensajeChat`, `PreguntaBloqueada`, etc.) - Django-created tables

### AI Integration Flow
1. **Question Validation**: `es_pregunta_valida()` filters HR-related questions
2. **SQL Generation**: `obtener_consulta_sql()` converts natural language to PostgreSQL queries using Claude AI
3. **Data Retrieval**: Execute generated SQL against the HR database
4. **Response Generation**: `generar_respuesta_final()` converts results back to natural language
5. **Metadata Extraction**: Parse JSON blocks from AI responses for UI interactions

### Key Models Relationships
```
contrato (main table)
├── id_persona → persona.id_persona
├── id_funcion → funcion.id_funcion  
└── id_tiempo → tiempo_contrato.id_tiempo

SesionChat (chat sessions)
├── usuario → User (Django auth)
└── MensajeChat (individual messages)
    └── DatosFuenteMensaje (source data in JSON)
```

## Configuration Requirements

### Environment Variables
- `ANTHROPIC_API_KEY`: Required for Claude AI integration
- Database credentials in `bot.py` (currently hardcoded for development)

### Database Setup
- PostgreSQL server on localhost:5432
- Database: "test"
- Must contain existing HR tables: `persona`, `funcion`, `tiempo_contrato`, `contrato`

## Special Features

### Term Exclusion System
Users can configure terms to exclude from search results. The AI automatically applies these exclusions when generating SQL queries using NOT LIKE conditions.

### Context Management
Admins can configure different AI system prompts via `ContextoPrompt` model. Only one context can be active at a time, affecting how the AI interprets and responds to questions.

### Session State Management
- **Active sessions**: Users can add new messages
- **Finalized sessions**: Read-only mode
- **Sessions with blocked questions**: Cannot be deleted (audit trail requirement)

### Data Source Transparency
Raw SQL results are stored in `DatosFuenteMensaje` and can be viewed by users to understand how AI responses were generated.

## Important Code Patterns

### Error Handling
Always use specific exception handling (e.g., `json.JSONDecodeError` instead of bare `except`).

### Security Considerations
- All views require `@login_required` decorator
- Admin functions use `@staff_member_required`
- Users can only access their own chat sessions
- SQL injection prevention through parameterized queries

### AI Response Processing
AI responses may contain JSON blocks at the end (e.g., `{"id_contrato": [12, 15, 18]}`) that are extracted for UI interactions like modal popups showing detailed information.

## File Structure Context

- `chatbot/bot.py`: Core AI integration and database interaction functions
- `chatbot/views.py`: Django views handling web interface and API endpoints
- `chatbot/models.py`: Database models (mix of managed and unmanaged)
- `chatbot/templates/`: HTML templates with Bootstrap 5 styling
- `chatbot_web/`: Django project configuration
- Utility scripts in root directory for database maintenance tasks