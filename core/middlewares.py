from datetime import datetime, timedelta
from django.shortcuts import redirect
from django.utils.deprecation import MiddlewareMixin
from contas.models import Licenca
from django.utils.timezone import now
from django.contrib.auth import authenticate, login, logout


class LicenseMiddleware(MiddlewareMixin):
    def process_request(self, request):
        # Ignorar a verificação para URLs de login e token
        if request.path in ['/auth/login/', '/auth/token/', '/auth/logout/', '/auth/signup/']:
            return None

        user = request.user

        # Se o usuário não estiver autenticado, não faz nada
        if not user.is_authenticated:
            return None

        # Se o usuário for staff, não precisa de licença
        if user.is_staff:
            return None

        # Verificar se há um token válido na sessão
        token_from_session = request.session.get('user_token')
        if not token_from_session:
            # Se não há token na sessão, redireciona para a página de inserção de token
            return redirect('token_entry')

        try:
            license = Licenca.objects.get(token=token_from_session, user=user)
            if not license.is_valid():
                # Se a licença não for válida, remove o token da sessão e redireciona
                request.session.pop('user_token', None)
                return redirect('token_entry')
        except Licenca.DoesNotExist:
            # Se a licença não existir, remove o token da sessão e redireciona
            request.session.pop('user_token', None)
            return redirect('token_entry')

        return None
    
class ForceLogoutMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        login_time = request.session.get('login_time')
        if login_time:
            login_time = datetime.fromisoformat(login_time)
            if now() > login_time + timedelta(seconds=1800):
                logout(request)
                return redirect('login')
        return self.get_response(request)
