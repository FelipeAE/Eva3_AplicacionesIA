from django.urls import path
from . import views

urlpatterns = [
    path('', views.chat_home, name='chat_home'),
    path('sesion/<int:id>/', views.chat_sesion, name='chat_sesion'),
    path('nueva/', views.nueva_sesion, name='nueva_sesion'),
    path('borrar/<int:id>/', views.borrar_sesion, name='borrar_sesion'),
    path('finalizar/<int:id>/', views.finalizar_sesion, name='finalizar_sesion'),
]
