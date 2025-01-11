from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from django.contrib.auth import views as auth_views
from contas.views import LoginView, SignUpView, LogOutView, TokenEntryView
from . import views

urlpatterns = [
    path('token/', TokenEntryView.as_view(), name='token_entry'),
    path('login/', LoginView.as_view(template_name='registration/login.html'), name='login'),
    path('logout/', LogOutView, name='logout'),
    path('signup/', SignUpView, name='signup'),
    path('reset_password/', auth_views.PasswordResetView.as_view(template_name='registration/password_reset.html'), name='reset_password'),
    path('reset_password_sent/', auth_views.PasswordResetDoneView.as_view(template_name='registration/password_reset_sent.html'), name='password_reset_done'),
    path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(template_name='registration/password_reset_form2.html'), name='password_reset_confirm'),
    path('reset_password_complete/', auth_views.PasswordResetCompleteView.as_view(template_name='registration/password_reset_done2.html'), name='password_reset_complete'),
    path('perfil/', views.PerfilView, name='perfil'),
    path('perfil/editar-perfil/', views.EditarPerfilView, name='editar_perfil'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)