from .chat_views import chat_home, chat_sesion, nueva_sesion, borrar_sesion, finalizar_sesion
from .admin_views import panel_admin, gestionar_contextos
from .auth_views import registro
from .api_views import detalle_contrato, detalle_generico
from .settings_views import excluir_terminos

__all__ = [
    'chat_home', 'chat_sesion', 'nueva_sesion', 'borrar_sesion', 'finalizar_sesion',
    'panel_admin', 'gestionar_contextos', 
    'registro',
    'detalle_contrato', 'detalle_generico',
    'excluir_terminos'
]