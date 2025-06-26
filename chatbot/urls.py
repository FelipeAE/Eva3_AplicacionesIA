from django.urls import path
from . import views

urlpatterns = [
    path('', views.chat_home, name='chat_home'),
    path('sesion/<int:id>/', views.chat_sesion, name='chat_sesion'),
    path('nueva/', views.nueva_sesion, name='nueva_sesion'),
    path('borrar/<int:id>/', views.borrar_sesion, name='borrar_sesion'),
    path('finalizar/<int:id>/', views.finalizar_sesion, name='finalizar_sesion'),
    path('excluir/', views.excluir_terminos, name='excluir_terminos'),
    path('contextos/', views.gestionar_contextos, name='gestionar_contextos'),
    path('detalle/<int:id>/', views.detalle_contrato, name='detalle_contrato'),
    path('detalle_generico/<str:tipo>/<int:id>/', views.detalle_generico, name='detalle_generico'),
    path('registro/', views.registro, name='registro'),
]
