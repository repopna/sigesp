from django.urls import path
from . import views


urlpatterns = [
    path('usuarios/', views.UsuariosJSONView.as_view(), name='dados_usuarios'),
    path('pedidos/', views.PedidosJSONView.as_view(), name='dados_pedido'),
]