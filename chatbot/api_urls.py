from django.urls import path
from .api import (
    # Chat APIs
    api_sessions_list,
    api_session_create,
    api_session_detail,
    api_send_message,
    api_session_finalize,
    api_session_delete,
    
    # Admin APIs
    api_contexts_list,
    api_context_create,
    api_context_activate,
    api_context_deactivate,
    api_context_delete,
    
    # User Settings APIs
    api_excluded_terms,
    api_excluded_term_add,
    api_excluded_term_delete,
)

# Existing API views
from .views.api_views import detalle_contrato, detalle_generico

urlpatterns = [
    # ==================== CHAT APIs ====================
    path('sessions/', api_sessions_list, name='api_sessions_list'),
    path('sessions/create/', api_session_create, name='api_session_create'),
    path('sessions/<int:session_id>/', api_session_detail, name='api_session_detail'),
    path('sessions/<int:session_id>/message/', api_send_message, name='api_send_message'),
    path('sessions/<int:session_id>/finalize/', api_session_finalize, name='api_session_finalize'),
    path('sessions/<int:session_id>/delete/', api_session_delete, name='api_session_delete'),
    
    # ==================== ADMIN APIs ====================
    path('admin/contexts/', api_contexts_list, name='api_contexts_list'),
    path('admin/contexts/create/', api_context_create, name='api_context_create'),
    path('admin/contexts/<int:context_id>/activate/', api_context_activate, name='api_context_activate'),
    path('admin/contexts/<int:context_id>/deactivate/', api_context_deactivate, name='api_context_deactivate'),
    path('admin/contexts/<int:context_id>/delete/', api_context_delete, name='api_context_delete'),
    
    # ==================== USER SETTINGS APIs ====================
    path('settings/excluded-terms/', api_excluded_terms, name='api_excluded_terms'),
    path('settings/excluded-terms/add/', api_excluded_term_add, name='api_excluded_term_add'),
    path('settings/excluded-terms/<int:term_id>/delete/', api_excluded_term_delete, name='api_excluded_term_delete'),
    
    # ==================== EXISTING APIs ====================
    path('contrato/<int:id>/', detalle_contrato, name='api_detalle_contrato'),
    path('detalle/<str:tipo>/<int:id>/', detalle_generico, name='api_detalle_generico'),
]