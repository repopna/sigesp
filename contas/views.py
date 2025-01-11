from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth.views import LoginView
from django.urls import reverse
from django.utils.text import slugify
from django.contrib.auth.decorators import login_required
from django.views import View
from contas.models import Centro, CustomUser, Dspo, Eps, Licenca, Psp, Sap
from notifications.signals import notify
from sigesp.settings import EMAIL_HOST_USER
from django.core.mail import send_mail
from notifications.models import Notification
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.forms import PasswordChangeForm
from .forms import CustomAuthenticationForm, TokenForm
from django.contrib.auth import authenticate, login as auth_login
from django.utils.timezone import now


# Create your views here.

class TokenEntryView(View):
    def get(self, request):
        form = TokenForm()
        return render(request, 'token_entry.html', {'form': form})

    def post(self, request):
        form = TokenForm(request.POST)
        if form.is_valid():
            token = form.cleaned_data['token']
            try:
                # Busca a licença pelo token e pelo usuário logado
                license = Licenca.objects.get(token=token, user=request.user)
                if not license.is_valid():
                    form.add_error(None, 'Token inválido ou expirado')
                else:
                    # Salva o token e a licença na sessão
                    request.session['user_token'] = str(token)
                    request.session['license_id'] = license.id
                    
                    self.request.session['login_time'] = now().isoformat()

                    # Atualizar a sessão atual da licença
                    license.logout_previous_session()

                    if not request.session.session_key:
                        request.session.create()
                    
                    license.current_session_key = request.session.session_key
                    license.save()

                    return redirect('index')  # Ou qualquer página que você deseje
            except Licenca.DoesNotExist:
                form.add_error(None, 'Token não encontrado ou não pertence à sua conta')
        return render(request, 'token_entry.html', {'form': form})

class LoginView(LoginView):
    template_name = 'registration/login.html'
    form_class = CustomAuthenticationForm

    def form_invalid(self, form):
        response = super().form_invalid(form)
        messages.error(self.request, '* Credenciais inválidas. Por favor, tente novamente.')
        return response

    def form_valid(self, form):
        user = form.get_user()
        auth_login(self.request, user)
        
        self.request.session['login_time'] = now().isoformat()

        if user.is_staff:
            return super().form_valid(form)
        
        # Redirecionar para a entrada de token após o login
        return redirect('token_entry')

    def get_success_url(self):
        return reverse('index')  
    
def get_encoded_filename(file):
    if file:
        filename, file_extension = file.name.rsplit('.', 1)
        filename_slug = slugify(filename)
        return f"{filename_slug}.{file_extension}"
    return None

def SignUpView(request):

    if request.method == 'POST':
        profile_type = request.POST['perfil']

        if profile_type == 'eps':
            nif = request.POST['NIF'].upper()
            username = request.POST['NIF'].upper()
            nome = request.POST['nome']
            email = request.POST['email'].lower()
            telefone = request.POST['telefone']
            morada = request.POST['morada']
            password = request.POST['password1']
            sg_nome = request.POST['sg_nome']
            sg_funcao = request.POST['sg_funcao']
            sg_id = request.POST['sg_id']
            sg_morada = request.POST['sg_morada']
            sg_email = request.POST['sg_email']
            sg_telefone = request.POST['sg_telefone']
            
            copia_licenca = request.FILES.get('copia_licenca')
            copia_licenca.name = get_encoded_filename(copia_licenca)

            certidao = request.FILES.get('certidao')
            certidao.name = get_encoded_filename(certidao)

            copia_bi_sg = request.FILES.get('copia_bi_sg')
            copia_bi_sg.name = get_encoded_filename(copia_bi_sg)

            foto_passe_sg = request.FILES.get('foto_passe_sg')
            foto_passe_sg.name = get_encoded_filename(foto_passe_sg)
            
            verify_username = CustomUser.objects.filter(username=username)
            verify_email = CustomUser.objects.filter(email=email)
            verify_telefone = CustomUser.objects.filter(telefone=telefone)

            if verify_username.exists():
                messages.error(request, '*Já exite um usuário cadastrado com este NIF.')
                return render(request, 'signup.html')
            
            if verify_email.exists():
                messages.error(request, '*Este email já está sendo usado.')
                return render(request, 'signup.html')
            
            if verify_telefone.exists():
                messages.error(request, '*Este número de telefone já está sendo usado.')
                return render(request, 'signup.html')
            
            user = CustomUser.objects.create_user(username=username, email=email, password=password, telefone=telefone , profile_type=profile_type)
            Eps.objects.create(user=user, nome=nome, nif=nif, morada=morada, sg_nome=sg_nome, sg_funcao=sg_funcao, sg_id=sg_id, sg_morada=sg_morada, sg_email=sg_email, sg_telefone=sg_telefone,
                copia_licenca=copia_licenca, certidao=certidao, copia_bi_sg=copia_bi_sg, foto_passe_sg=foto_passe_sg)

            subject = f'Novo Cadastro | Empresa Privada de Segurança'
            message = f'A empresa {nome} de NIF {username} acabou de se cadastrar e aguarda à sua verificação.'
            sender = EMAIL_HOST_USER
            recipients = [EMAIL_HOST_USER]
            send_mail(subject, message, sender, recipients)

            notify.send(user, recipient=user, verb=f"Seja bem vindo ao SIGESP {nome}. A sua conta estará a ser verificada pelos especialistas o mais breve possível afim de poder exercer às actividades de Segurança Privada.")

        elif profile_type == 'sap':
            nif = request.POST['NIF'].upper()
            username = request.POST['NIF'].upper()
            nome = request.POST['nome']
            email = request.POST['email'].lower()
            telefone = request.POST['telefone']
            morada = request.POST['morada']
            password = request.POST['password1']
            sg_nome = request.POST['sg_nome']
            sg_funcao = request.POST['sg_funcao']
            sg_id = request.POST['sg_id']
            sg_morada = request.POST['sg_morada']
            sg_email = request.POST['sg_email']
            sg_telefone = request.POST['sg_telefone']

            copia_licenca = request.FILES.get('copia_licenca')
            copia_licenca.name = get_encoded_filename(copia_licenca)

            certidao = request.FILES.get('certidao')
            certidao.name = get_encoded_filename(certidao)

            copia_bi_sg = request.FILES.get('copia_bi_sg')
            copia_bi_sg.name = get_encoded_filename(copia_bi_sg)

            foto_passe_sg = request.FILES.get('foto_passe_sg')
            foto_passe_sg.name = get_encoded_filename(foto_passe_sg)
            
            verify_username = CustomUser.objects.filter(username=username)
            verify_email = CustomUser.objects.filter(email=email)
            verify_telefone = CustomUser.objects.filter(telefone=telefone)

            if verify_username.exists():
                messages.error(request, '*Já exite um usuário cadastrado com este NIF.')
                return render(request, 'signup.html')
            
            if verify_email.exists():
                messages.error(request, '*Este email já está sendo usado.')
                return render(request, 'signup.html')
            
            if verify_telefone.exists():
                messages.error(request, '*Este número de telefone já está sendo usado.')
                return render(request, 'signup.html')
            
            user = CustomUser.objects.create_user(username=username, email=email, password=password, telefone=telefone , profile_type=profile_type)
            Sap.objects.create(user=user, nome=nome, nif=nif, morada=morada, sg_nome=sg_nome, sg_funcao=sg_funcao, sg_id=sg_id, sg_morada=sg_morada, sg_email=sg_email, sg_telefone=sg_telefone,
                copia_licenca=copia_licenca, certidao=certidao, copia_bi_sg=copia_bi_sg, foto_passe_sg=foto_passe_sg)
            
            subject = f'Novo Cadastro | Centro de Formação'
            message = f'A empresa {nome} de NIF {username} acabou de se cadastrar e aguarda à sua verificação.'
            sender = EMAIL_HOST_USER
            recipients = [EMAIL_HOST_USER]
            send_mail(subject, message, sender, recipients)

            notify.send(user, recipient=user, verb=f"Seja bem vindo ao SIGESP {nome}. A sua conta estará a ser verificada pelos especialistas o mais breve possível afim de poder exercer às actividades de Segurança Privada.")

        elif profile_type == 'psp':
            username = request.POST['documento_id'].upper()
            nome = request.POST['nome']
            documento_id = request.POST['documento_id'].upper()
            email = request.POST['email'].lower()
            telefone = request.POST['telefone']
            estado_civil = request.POST['estado_civil']
            morada = request.POST['morada']
            password = request.POST['password1']
            documento = request.POST['documento']
            vinculo_checkbox = request.POST.get('vinculo')
            funcao = request.POST['funcao']
            sub_funcao = request.POST['sub_vigilante']

            if vinculo_checkbox == 'on':
                vinculo = True
            else:
                vinculo = False

            nome_empresa = request.POST['nome_empresa']
            funcao_empresa = request.POST['funcao_empresa']  
            
            prof_independente_checkbox = request.POST.get('prof_independente')

            if prof_independente_checkbox == 'on':
                prof_independente = True
            else:
                prof_independente = False

            agregado_familiar = request.FILES.get('agregado_familiar')

            if agregado_familiar:
                agregado_familiar.name = get_encoded_filename(agregado_familiar)
            
            documento_id_file = request.FILES.get('documento_id_file')
            documento_id_file.name = get_encoded_filename(documento_id_file)
            
            declaracao_servico = request.FILES.get('declaracao_servico')
            declaracao_servico.name = get_encoded_filename(declaracao_servico)
            
            foto_passe = request.FILES.get('foto_passe')
            foto_passe.name = get_encoded_filename(foto_passe)

            verify_username = CustomUser.objects.filter(username=username)
            verify_email = CustomUser.objects.filter(email=email)
            verify_telefone = CustomUser.objects.filter(telefone=telefone)
            
            if verify_username.exists():
                messages.error(request, '*Já exite um usuário cadastrado com este Documento.')
                return render(request, 'signup.html')
            
            if verify_email.exists():
                messages.error(request, '*Este email já está sendo usado.')
                return render(request, 'signup.html')
            
            if verify_telefone.exists():
                messages.error(request, '*Este número de telefone já está sendo usado.')
                return render(request, 'signup.html')
            
            user = CustomUser.objects.create_user(username=username, email=email, password=password, telefone=telefone , profile_type=profile_type)
            Psp.objects.create(user=user, nome=nome, funcao=funcao, sub_funcao=sub_funcao, documento=documento, documento_id=documento_id, vinculo=vinculo,
                prof_independente=prof_independente, nome_empresa=nome_empresa, funcao_empresa=funcao_empresa, morada=morada,
                declaracao_servico=declaracao_servico, foto_passe=foto_passe, documento_id_file=documento_id_file, estado_civil=estado_civil, agregado_familiar=agregado_familiar)

            subject = f'Novo Cadastro | Profissional de Segurança Privada'
            message = f'O Profissional de Segurança Privada {nome} acabou de se cadastrar e aguarda à sua verificação.'
            sender = EMAIL_HOST_USER
            recipients = [EMAIL_HOST_USER]
            send_mail(subject, message, sender, recipients)

            notify.send(user, recipient=user, verb=f"Seja bem vindo ao SIGESP {nome}. A sua conta estará a ser verificada pelos especialistas o mais breve possível afim de poder exercer às actividades de Segurança Privada.")

        elif profile_type == 'dspo':
            username = request.POST['nip'].upper()
            nome = request.POST['nome']
            comando = request.POST['comando']
            email = request.POST['email'].lower()
            telefone = request.POST['telefone']
            morada = request.POST['morada']
            password = request.POST['password1']
            funcao = request.POST['funcao']

            foto_passe = request.FILES.get('foto_passe')
            foto_passe.name = get_encoded_filename(foto_passe)

            verify_username = CustomUser.objects.filter(username=username)
            verify_email = CustomUser.objects.filter(email=email)
            verify_telefone = CustomUser.objects.filter(telefone=telefone)
            
            if verify_username.exists():
                messages.error(request, '*Já exite um usuário cadastrado com este NIP.')
                return render(request, 'signup.html')
            
            if verify_email.exists():
                messages.error(request, '*Este email já está sendo usado.')
                return render(request, 'signup.html')
            
            if verify_telefone.exists():
                messages.error(request, '*Este número de telefone já está sendo usado.')
                return render(request, 'signup.html')
            
            user = CustomUser.objects.create_user(username=username, email=email, password=password, telefone=telefone , profile_type=profile_type)
            Dspo.objects.create(user=user, nome=nome, nip=username, comando=comando, morada=morada, funcao=funcao, foto_passe=foto_passe)

            subject = f'Novo Cadastro | Técnico Provincial'
            message = f'O Técnico Provincial {nome} acabou de se cadastrar e aguarda à sua verificação.'
            sender = EMAIL_HOST_USER
            recipients = [EMAIL_HOST_USER]
            send_mail(subject, message, sender, recipients)

            notify.send(user, recipient=user, verb=f"Seja bem vindo ao SIGESP {nome}. A sua conta estará a ser verificada pelos especialistas o mais breve possível afim de poder exercer às actividades de Segurança Privada.")

        elif profile_type == 'centro':
            nif = request.POST['NIF']
            username = request.POST['NIF']
            nome = request.POST['nome']
            email = request.POST['email']
            telefone = request.POST['telefone']
            morada = request.POST['morada']
            password = request.POST['password1']
            sg_nome = request.POST['sg_nome']
            sg_funcao = request.POST['sg_funcao']
            sg_id = request.POST['sg_id']
            sg_morada = request.POST['sg_morada']
            sg_email = request.POST['sg_email']
            sg_telefone = request.POST['sg_telefone']
            
            copia_licenca = request.FILES.get('copia_licenca')
            copia_licenca.name = get_encoded_filename(copia_licenca)

            certidao = request.FILES.get('certidao')
            certidao.name = get_encoded_filename(certidao)

            copia_bi_sg = request.FILES.get('copia_bi_sg')
            copia_bi_sg.name = get_encoded_filename(copia_bi_sg)

            foto_passe_sg = request.FILES.get('foto_passe_sg')
            foto_passe_sg.name = get_encoded_filename(foto_passe_sg)
            
            verify_username = CustomUser.objects.filter(username=username)
            verify_email = CustomUser.objects.filter(email=email)
            verify_telefone = CustomUser.objects.filter(telefone=telefone)

            if verify_username.exists():
                messages.error(request, '*Já exite um usuário cadastrado com este NIF.')
                return render(request, 'signup.html')
            
            if verify_email.exists():
                messages.error(request, '*Este email já está sendo usado.')
                return render(request, 'signup.html')
            
            if verify_telefone.exists():
                messages.error(request, '*Este número de telefone já está sendo usado.')
                return render(request, 'signup.html')
            
            user = CustomUser.objects.create_user(username=username, email=email, password=password, telefone=telefone , profile_type=profile_type)
            Centro.objects.create(user=user, nome=nome, nif=nif, morada=morada, sg_nome=sg_nome, sg_funcao=sg_funcao, sg_id=sg_id, sg_morada=sg_morada, sg_email=sg_email, sg_telefone=sg_telefone,
                copia_licenca=copia_licenca, certidao=certidao, copia_bi_sg=copia_bi_sg, foto_passe_sg=foto_passe_sg)

            subject = f'Novo Cadastro | Centro de Formação'
            message = f'A empresa {nome} de NIF {username} acabou de se cadastrar e aguarda à sua verificação.'
            sender = EMAIL_HOST_USER
            recipients = [EMAIL_HOST_USER]
            send_mail(subject, message, sender, recipients)

            notify.send(user, recipient=user, verb=f"Seja bem vindo ao SIGESP {nome}. A sua conta estará a ser verificada pelos especialistas o mais breve possível afim de poder exercer às actividades de Segurança Privada.")

        user = authenticate(request, username=username, password=password)

        if user:
            login(request, user)
            return redirect('index')
        
    return render(request, 'signup.html')

def LogOutView(request):
    request.session.pop('user_token', None)
    logout(request)
    return redirect('/auth/login/')

@login_required
def PerfilView(request):
    notificacoes = Notification.objects.filter(recipient=request.user).order_by('-timestamp')
    notificacoes_n_lidas = notificacoes.filter(unread=True).count()

    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)
            messages.success(request, 'Sua palavra-passe foi alterada com sucesso!')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f'Erro em {field}: {error}')

    return render(request, 'perfil.html', {'notificacoes_n_lidas' : notificacoes_n_lidas} )

@login_required
def EditarPerfilView(request):
    notificacoes = Notification.objects.filter(recipient=request.user).order_by('-timestamp')
    notificacoes_n_lidas = notificacoes.filter(unread=True).count()
    return render(request, 'editar_perfil.html', {'notificacoes_n_lidas' : notificacoes_n_lidas})