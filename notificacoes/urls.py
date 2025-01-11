from django.conf import settings
from django.conf.urls.static import static
from django.urls import path
from . import views

urlpatterns = [

    path('', views.NotificacoesView, name='notificacoes'),
    path('ler_tudo', views.LerTudoView, name='ler_tudo'),
    path('mark_as_read/<int:notification_id>/', views.mark_as_read, name='mark_as_read'),
    
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)