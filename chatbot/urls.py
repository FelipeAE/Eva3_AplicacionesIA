from django.urls import path, include
# Import from new modular views architecture
from .views import (
    chat_home, chat_sesion, nueva_sesion, borrar_sesion, finalizar_sesion,
    panel_admin, gestionar_contextos,
    registro,
    detalle_contrato, detalle_generico,
    excluir_terminos
)

urlpatterns = [
    # ==================== WEB VIEWS ====================
    path('', chat_home, name='chat_home'),
    path('sesion/<int:id>/', chat_sesion, name='chat_sesion'),
    path('nueva/', nueva_sesion, name='nueva_sesion'),
    path('borrar/<int:id>/', borrar_sesion, name='borrar_sesion'),
    path('finalizar/<int:id>/', finalizar_sesion, name='finalizar_sesion'),
    path('excluir/', excluir_terminos, name='excluir_terminos'),
    path('contextos/', gestionar_contextos, name='gestionar_contextos'),
    path('admin-panel/', panel_admin, name='admin_panel'),
    path('detalle/<int:id>/', detalle_contrato, name='detalle_contrato'),
    path('detalle_generico/<str:tipo>/<int:id>/', detalle_generico, name='detalle_generico'),
    path('registro/', registro, name='registro'),
    
    # ==================== REST APIs ====================
    path('api/v1/', include('chatbot.api_urls')),
]
