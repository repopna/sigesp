from django.conf import settings
from django.contrib import admin
from django.urls import include, path
from django.conf.urls.static import static


urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('core.urls')),
    path('auth/', include('contas.urls')),
    path('notificacoes/', include('notificacoes.urls')),
    path('dados/', include('dados.urls')),
    
]  + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
