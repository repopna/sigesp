from django.utils import timezone
from django.http import HttpResponseForbidden, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.text import slugify
from django.contrib import messages
from notifications.signals import notify
from contas.models import Centro, CustomUser, Dspo, Eps, Licenca, Psp, Sap, TecnicoDISPO
from logs.models import Logs
from sigesp.settings import BASE_DIR, EMAIL_HOST_USER
from core.models import CarteiraProfissional, Denuncias, EmissaoMultas, EmissaoRelatorios, Formacoes, ListaEnvolvidosCrime, MapaArmas, MapaPessoal, MapaPostos, Pedido, RegistroPonto, Relatorio, SolicitacaoLicenca
from django.core.mail import send_mail
from notifications.models import Notification
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from datetime import datetime, timedelta
from io import BytesIO
import os
from django.http import HttpResponse
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase import pdfmetrics
from sigesp import settings
from reportlab.lib.colors import HexColor
from reportlab.graphics.shapes import Drawing, Polygon
from reportlab.graphics import renderPDF
from reportlab.platypus import Paragraph
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_JUSTIFY
from reportlab.lib.units import mm
from django.db.models import Q
import requests
from django.utils.timezone import now



# Create your views here.

def get_encoded_filename(file):
    if file:
        filename, file_extension = file.name.rsplit('.', 1)
        filename_slug = slugify(filename)
        return f"{filename_slug}.{file_extension}"
    return None

def mascarar_uuid(uuid_str):
    if len(uuid_str) < 16:
        return uuid_str

    partes = [
        '*' * 6 + uuid_str[6:8],
        '*' * 2 + uuid_str[10:12],
        '*' * 4 + uuid_str[16:20],
        uuid_str[20:22] + '*' * 3,
        uuid_str[22:]
    ]

    return '-'.join(partes)

@login_required
def IndexView(request):
    notificacoes = Notification.objects.filter(recipient=request.user).order_by('-timestamp')
    notificacoes_n_lidas = notificacoes.filter(unread=True).count()
    user = request.user

    if  user.profile_type == 'tecdsp':

        pedidos = Pedido.objects.all()
        pedidos_enviados = pedidos.filter().count()
        pedidos_aceites = pedidos.filter(status_pedido='aceite').count()
        pedidos_rejeitados = pedidos.filter(status_pedido='recusado').count()
        pedidos_em_processamento = pedidos.filter(status_pedido='em_processamento').count()
        
        eps = Eps.objects.all()
        sap = Sap.objects.all()
        centro = Centro.objects.all()
        psp = Psp.objects.all()

        qty_eps = eps.filter().count()
        qty_sap = sap.filter().count()
        qty_centro = centro.filter().count()
        qty_psp = psp.filter().count()

        context = {
            'notificacoes_n_lidas' : notificacoes_n_lidas,
            'pedidos_enviados': pedidos_enviados,
            'pedidos_aceites': pedidos_aceites,
            'pedidos_rejeitados': pedidos_rejeitados,
            'pedidos_em_processamento': pedidos_em_processamento,
            'user':user,
            'qty_eps':qty_eps,
            'qty_sap':qty_sap,
            'qty_centros':qty_centro,
            'qty_psp':qty_psp,
        }

        return render(request, 'painel.html', context)
    
    if  user.profile_type == 'dspo':
        context = {
            'user':user,
        }
        return render(request, 'painel.html', context)


    pedidos = Pedido.objects.filter(entidade=request.user)
    pedidos_enviados = pedidos.filter(entidade=request.user).count()
    pedidos_aceites = pedidos.filter(status_pedido='aceite').count()
    pedidos_rejeitados = pedidos.filter(status_pedido='recusado').count()
    pedidos_em_processamento = pedidos.filter(status_pedido='em_processamento').count()
    license_id = request.session.get('license_id')
    license = get_object_or_404(Licenca, id=license_id)
    uuid_mascarado = mascarar_uuid(str(license.token))

    login_time = request.session.get('login_time')
    if login_time:
        login_time = now() - timedelta(seconds=1800)  # Ajustar o tempo se necessário
        expiration_time = (login_time + timedelta(seconds=1800)).isoformat()
    else:
        expiration_time = None


    context = {
        'notificacoes_n_lidas' : notificacoes_n_lidas,
        'pedidos_enviados': pedidos_enviados,
        'pedidos_aceites': pedidos_aceites,
        'pedidos_rejeitados': pedidos_rejeitados,
        'pedidos_em_processamento': pedidos_em_processamento,
        'user':user,
        'license_id': license_id,
        'dias_restantes': license.dias_restantes(),
        'uuid_mascarado': uuid_mascarado,
        'expiration_time': expiration_time,
    }

    if request.method == 'POST':
        form = request.POST['form']

        if form == 'verify':
            
            tecnicos_dispo = TecnicoDISPO.objects.all()

            for tecnico in tecnicos_dispo:
                notify.send(request.user, recipient=tecnico.user, verb=f"{request.user} Solicita uma verificação no seu perfil.")

            messages.success(request, 'Solicitação enviada com sucesso, por favor aguarde.')
            return render(request, 'painel.html', {'notificacoes_n_lidas' : notificacoes_n_lidas})

    return render(request, 'painel.html', context)

@login_required
def SolicitacaoLicencaView(request):
    notificacoes = Notification.objects.filter(recipient=request.user).order_by('-timestamp')
    notificacoes_n_lidas = notificacoes.filter(unread=True).count()

    if request.method == 'POST':
        categoria = request.POST['categoria']
        pedido = request.POST['pedido']
        motivo = request.POST['motivo']
        
        curriculum_vitae = request.FILES.get('curriculum_vitae')
        curriculum_vitae.name = get_encoded_filename(curriculum_vitae)

        certificado = request.FILES.get('certificado')
        certificado.name = get_encoded_filename(certificado)

        copia_bi = request.FILES.get('copia_bi')
        copia_bi.name = get_encoded_filename(copia_bi)

        registro_criminal = request.FILES.get('registro_criminal')
        registro_criminal.name = get_encoded_filename(registro_criminal)

        comprovativo = request.FILES.get('comprovativo')
        comprovativo.name = get_encoded_filename(comprovativo)

        if not categoria:
            messages.error(request, 'Insira a categoria a requerer')
            return render(request, 'views/solicitacao_licenca_view.html', {'notificacoes_n_lidas' : notificacoes_n_lidas})
        
        if not pedido:
            messages.error(request, 'Insira o pedido')
            return render(request, 'views/solicitacao_licenca_view.html', {'notificacoes_n_lidas' : notificacoes_n_lidas})
        
        SolicitacaoLicenca.objects.create(autor=request.user, categoria=categoria, pedido=pedido, motivo=motivo, curriculum_vitae=curriculum_vitae,
            certificado=certificado, copia_bi=copia_bi, registro_criminal=registro_criminal, comprovativo=comprovativo)
        
        subject = f'Nova Solicitação de Licença'
        message = f'Foi enviado uma nova solicitação de licença.'
        sender = EMAIL_HOST_USER
        recipients = [EMAIL_HOST_USER]
        send_mail(subject, message, sender, recipients)

        notify.send(request.user, recipient=request.user, verb=f"A sua solicitação de Carteira Profissional foi enviada com sucesso.")

        messages.success(request, "Solicitação envida com sucesso.")
        return render(request, 'views/solicitacao_licenca_view.html', {'notificacoes_n_lidas' : notificacoes_n_lidas})
         
    return render(request, 'views/solicitacao_licenca_view.html', {'notificacoes_n_lidas' : notificacoes_n_lidas})

@login_required
def SolicitacoesLicencasEnviadasView(request):
    notificacoes = Notification.objects.filter(recipient=request.user).order_by('-timestamp')
    notificacoes_n_lidas = notificacoes.filter(unread=True).count()
    slis = SolicitacaoLicenca.objects.all()
    return render(request, 'views/solicitacoes_licencas_enviadas_view.html', {'notificacoes_n_lidas' : notificacoes_n_lidas, 'slis': slis})

@login_required
@require_http_methods(["DELETE"])
def remover_sli(request, sli_id):
    
    sli = get_object_or_404(SolicitacaoLicenca, pk=sli_id)
    sli.delete()
    return JsonResponse({'message': 'Cadastro removido com sucesso.'})

@login_required
def MapaPessoalView(request):
    notificacoes = Notification.objects.filter(recipient=request.user).order_by('-timestamp')
    notificacoes_n_lidas = notificacoes.filter(unread=True).count()
    pessoal = MapaPessoal.objects.filter(entidade=request.user)


    if request.method == 'POST':
        nome = request.POST['nome']
        sexo = request.POST['sexo']
        numero_bi = request.POST['numero_bi']
        funcao = request.POST['funcao']
        estado_civil = request.POST['estado_civil']
        tempo_servico = request.POST['tempo_servico']
        data_nascimento = request.POST['data_nascimento']

        verify_bi = MapaPessoal.objects.filter(numero_bi=numero_bi)

        if not estado_civil:
            messages.error(request, 'Insira o estado civil')
            return render(request, 'views/mapa_pessoal_view.html', {'notificacoes_n_lidas' : notificacoes_n_lidas, 'pessoal': pessoal})

        if verify_bi.exists():
            messages.error(request, '*Já existe alguém cadastrado com esse Número de BI')
            return render(request, 'views/mapa_pessoal_view.html', {'notificacoes_n_lidas' : notificacoes_n_lidas, 'pessoal': pessoal})
    
        pessoa = MapaPessoal.objects.create(
            entidade=request.user,
            nome=nome,
            sexo=sexo,
            estado_civil=estado_civil,
            numero_bi=numero_bi,
            funcao=funcao,
            tempo_servico=tempo_servico,
            data_nascimento=data_nascimento
        )

        messages.success(request, 'Cadastro efectuado com sucesso')
        return render(request, 'views/mapa_pessoal_view.html', {'notificacoes_n_lidas' : notificacoes_n_lidas, 'pessoal': pessoal})

    return render(request, 'views/mapa_pessoal_view.html', {'notificacoes_n_lidas' : notificacoes_n_lidas, 'pessoal': pessoal})

@login_required
def MapaArmasView(request):
    notificacoes = Notification.objects.filter(recipient=request.user).order_by('-timestamp')
    notificacoes_n_lidas = notificacoes.filter(unread=True).count()
    armas = MapaArmas.objects.filter(entidade=request.user)
        
    if request.method == 'POST':
        numero = request.POST['numero_arma'].upper()

        try:
            api_url = f"http://sigae.kirene.ao/api/manifesto/{numero}/"
            
            # Fazendo a requisição GET à API
            response = requests.get(api_url)
            
            # Se o status da resposta for 200, retorna os dados
            if response.status_code == 200:
            
                classificacao = request.POST['classificacao']
                marca = request.POST['marca']
                origem = request.POST['origem']
                calibre = request.POST['calibre']
                cano = request.POST['cano']
                tiro = request.POST['tiro']
                comprimento_cano = request.POST['comprimento_cano']
                alma = request.POST['alma']
                percussao = request.POST['percussao']
                culatra = request.POST['culatra']
                caes = request.POST['caes']
                platinas = request.POST['platinas']
                    
                verify_na = MapaArmas.objects.filter(numero_arma=numero)
                    
                if verify_na.exists():
                    messages.error(request, 'Esta arma já está cadastrada')
                    return render(request, 'views/mapa_armas_view.html', {'notificacoes_n_lidas' : notificacoes_n_lidas, 'armas': armas})
                    
                arma = MapaArmas.objects.create(
                    entidade=request.user,
                    numero_arma=numero,
                    classificacao=classificacao,
                    marca=marca,
                    origem=origem,
                    calibre=calibre,
                    cano=cano,
                    tiro=tiro,
                    comprimento_cano=comprimento_cano,
                    alma=alma,
                    percussao=percussao,
                    culatra=culatra,
                    caes=caes,
                    platinas=platinas,
                    data_registro=timezone.now()
                )
                messages.success(request, 'Armas cadastrada com sucesso')
                return render(request, 'views/mapa_armas_view.html', {'notificacoes_n_lidas' : notificacoes_n_lidas, 'armas': armas})
            
            else:
                messages.error(request, 'Esta arma não está cadastrada no Departamento de Armas e Explosivos')
                return render(request, 'views/mapa_armas_view.html', {'notificacoes_n_lidas' : notificacoes_n_lidas, 'armas': armas})

        except requests.exceptions.RequestException as e:
            # Captura qualquer erro de conexão ou requisição
            return HttpResponse(f"Erro ao consultar informações da arma: {e}", status=500)

        


    return render(request, 'views/mapa_armas_view.html', {'notificacoes_n_lidas' : notificacoes_n_lidas, 'armas': armas})

@login_required
def MapaPostosView(request):
    notificacoes = Notification.objects.filter(recipient=request.user).order_by('-timestamp')
    notificacoes_n_lidas = notificacoes.filter(unread=True).count()
    user =  request.user
    postos =  MapaPostos.objects.filter(entidade=user)

    context = {
        'notificacoes_n_lidas': notificacoes_n_lidas,
        'user': user,
        'postos': postos,
    }
    
    if request.method == 'POST':
        ficheiro = request.FILES.get('ficheiro')
        ficheiro.name = get_encoded_filename(ficheiro)


        posto = MapaPostos.objects.create(
            entidade=user,
            ficheiro=ficheiro
        )
        messages.success(request, 'Cadastro efectuado com sucesso')

    return render(request, 'views/mapa_postos_view.html', context)

@login_required
def ArmaView(request, mapaarmas_id):
    notificacoes = Notification.objects.filter(recipient=request.user).order_by('-timestamp')
    notificacoes_n_lidas = notificacoes.filter(unread=True).count()
    user = request.user

    if user.profile_type == 'tecdsp':
        arma = get_object_or_404(MapaArmas, id=mapaarmas_id)
        return render(request, 'views/arma_view.html', {'arma': arma, 'notificacoes_n_lidas': notificacoes_n_lidas})

    arma = get_object_or_404(MapaArmas, id=mapaarmas_id, entidade=request.user)
    return render(request, 'views/arma_view.html', {'arma': arma, 'notificacoes_n_lidas': notificacoes_n_lidas})

@login_required
def EmissaoMultasView(request):
    notificacoes = Notification.objects.filter(recipient=request.user).order_by('-timestamp')
    notificacoes_n_lidas = notificacoes.filter(unread=True).count()

    if request.method == 'POST':
        ficheiro = request.FILES.get('ficheiro')
        ficheiro.name = get_encoded_filename(ficheiro)
        dspo = get_object_or_404(Dspo, user=request.user)
        comando = dspo.comando

        multa = EmissaoMultas.objects.create(
            autor = request.user, ficheiro=ficheiro, provincia=comando
        )

        messages.success(request, 'Multa enviada com sucesso')
        return render(request, 'views/emissao_multas_view.html', {'notificacoes_n_lidas' : notificacoes_n_lidas})

    return render(request, 'views/emissao_multas_view.html', {'notificacoes_n_lidas' : notificacoes_n_lidas})

@login_required
def EmissaoRelatoriosView(request):
    notificacoes = Notification.objects.filter(recipient=request.user).order_by('-timestamp')
    notificacoes_n_lidas = notificacoes.filter(unread=True).count()

    if request.method == 'POST':
        ficheiro = request.FILES.get('ficheiro')
        ficheiro.name = get_encoded_filename(ficheiro)
        dspo = get_object_or_404(Dspo, user=request.user)
        comando = dspo.comando

        relatorio = EmissaoRelatorios.objects.create(
            autor = request.user, ficheiro=ficheiro, provincia=comando
        )

        messages.success(request, 'Relatório enviado com sucesso')
        return render(request, 'views/emissao_relatorios_view.html', {'notificacoes_n_lidas' : notificacoes_n_lidas})
    
    return render(request, 'views/emissao_relatorios_view.html', {'notificacoes_n_lidas' : notificacoes_n_lidas})

@login_required
def DenunciasView(request):
    notificacoes = Notification.objects.filter(recipient=request.user).order_by('-timestamp')
    notificacoes_n_lidas = notificacoes.filter(unread=True).count()

    pessoal = MapaPessoal.objects.filter(entidade=request.user)

    if request.method == 'POST':
        tipo = request.POST['tipo']
        acusado = request.POST['acusado']
        descricao = request.POST['descricao']
        
        if not tipo:
            messages.error(request, 'Insira o tipo de comunicação')
            return render(request, 'views/denuncias_view.html', {'notificacoes_n_lidas' : notificacoes_n_lidas, 'pessoal': pessoal})
        
        if not descricao:
            messages.error(request, 'Insira a descrição da comunicação')
            return render(request, 'views/denuncias_view.html', {'notificacoes_n_lidas' : notificacoes_n_lidas, 'pessoal': pessoal})


        denuncia = Denuncias.objects.create(
            autor = request.user, tipo_de_denuncia=tipo, acusado=acusado, descricao=descricao
        )
        
        notify.send(request.user, recipient=request.user, verb=f"A sua comunicação foi enviada com sucesso, este é o código da sua comunicação #{denuncia.id}.")

        subject = f'Nova Comunicação | #{denuncia.id}'
        message = f'Foi enviado uma nova comunicação no SIGESP.'
        sender = EMAIL_HOST_USER
        recipients = [EMAIL_HOST_USER]
        send_mail(subject, message, sender, recipients)

        messages.success(request, 'Comunicação enviada com sucesso')
        return render(request, 'views/denuncias_view.html', {'notificacoes_n_lidas' : notificacoes_n_lidas, 'pessoal': pessoal})
    
    return render(request, 'views/denuncias_view.html', {'notificacoes_n_lidas' : notificacoes_n_lidas, 'pessoal': pessoal})

@login_required
def DenunciasEnviadasView(request):
    notificacoes = Notification.objects.filter(recipient=request.user).order_by('-timestamp')
    notificacoes_n_lidas = notificacoes.filter(unread=True).count()

    denuncias = Denuncias.objects.all()

    return render(request, 'views/denuncias_enviadas_view.html', {'notificacoes_n_lidas' : notificacoes_n_lidas, 'denuncias': denuncias})

@login_required
def AvaliacaoValidacaoView(request):
    notificacoes = Notification.objects.filter(recipient=request.user).order_by('-timestamp')
    notificacoes_n_lidas = notificacoes.filter(unread=True).count()

    if request.method == 'POST':
        user = request.user

        if user.profile_type == 'eps':
            empresa = Eps.objects.get(user=user)

            alvara_comercial = request.FILES.get('alvara_comercial')
            alvara_comercial.name = get_encoded_filename(alvara_comercial)
            certificado_registro = request.FILES.get('certificado_registro')
            certificado_registro.name = get_encoded_filename(certificado_registro)
            atestado_sociedade = request.FILES.get('atestado_sociedade')
            atestado_sociedade.name = get_encoded_filename(atestado_sociedade)
            croquis_localizacao = request.FILES.get('croquis_localizacao')
            croquis_localizacao.name = get_encoded_filename(croquis_localizacao)
            certificado_registro2 = request.FILES.get('certificado_registro2')
            certificado_registro2.name = get_encoded_filename(certificado_registro2)
            comprovativo_existência = request.FILES.get('comprovativo_existência')
            comprovativo_existência.name = get_encoded_filename(comprovativo_existência)
            
            empresa.alvara_comercial = alvara_comercial
            empresa.certificado_registro = certificado_registro
            empresa.atestado_sociedade = atestado_sociedade
            empresa.croquis_localizacao = croquis_localizacao
            empresa.certificado_registro2 = certificado_registro2
            empresa.comprovativo_existência = comprovativo_existência

            empresa.save()

            subject = f'Avaliação e Validação dos Documentos | Empresa de Segurança Privada'
            message = f'A empresa {empresa.nome} de NIF {user.username} enviou os documentos para a verificação da sua conta.'
            sender = EMAIL_HOST_USER
            recipients = [EMAIL_HOST_USER]
            send_mail(subject, message, sender, recipients)

            messages.success(request, 'Documentos enviados com sucesso')
            return render(request, 'views/avaliacao_validacao_view.html', {'notificacoes_n_lidas' : notificacoes_n_lidas})
            
        elif user.profile_type == 'sap':
            empresa = Sap.objects.get(user=user)

            alvara_comercial = request.FILES.get('alvara_comercial')
            alvara_comercial.name = get_encoded_filename(alvara_comercial)
            certificado_registro = request.FILES.get('certificado_registro')
            certificado_registro.name = get_encoded_filename(certificado_registro)
            atestado_sociedade = request.FILES.get('atestado_sociedade')
            atestado_sociedade.name = get_encoded_filename(atestado_sociedade)
            croquis_localizacao = request.FILES.get('croquis_localizacao')
            croquis_localizacao.name = get_encoded_filename(croquis_localizacao)
            certificado_registro2 = request.FILES.get('certificado_registro2')
            certificado_registro2.name = get_encoded_filename(certificado_registro2)
            comprovativo_existência = request.FILES.get('comprovativo_existência')
            comprovativo_existência.name = get_encoded_filename(comprovativo_existência)
            
            empresa.alvara_comercial = alvara_comercial
            empresa.certificado_registro = certificado_registro
            empresa.atestado_sociedade = atestado_sociedade
            empresa.croquis_localizacao = croquis_localizacao
            empresa.certificado_registro2 = certificado_registro2
            empresa.comprovativo_existência = comprovativo_existência

            empresa.save()

            subject = f'Avaliação e Validação dos Documentos | Sistema de Auto Proteção'
            message = f'A empresa {empresa.nome} de NIF {user.username} enviou os documentos para a verificação da sua conta.'
            sender = EMAIL_HOST_USER
            recipients = [EMAIL_HOST_USER]
            send_mail(subject, message, sender, recipients)

            messages.success(request, 'Documentos enviados com sucesso')
            return render(request, 'views/avaliacao_validacao_view.html', {'notificacoes_n_lidas' : notificacoes_n_lidas})
        
        elif user.profile_type == 'centro':
            empresa = Centro.objects.get(user=user)

            alvara_comercial = request.FILES.get('alvara_comercial')
            alvara_comercial.name = get_encoded_filename(alvara_comercial)
            certificado_registro = request.FILES.get('certificado_registro')
            certificado_registro.name = get_encoded_filename(certificado_registro)
            atestado_sociedade = request.FILES.get('atestado_sociedade')
            atestado_sociedade.name = get_encoded_filename(atestado_sociedade)
            croquis_localizacao = request.FILES.get('croquis_localizacao')
            croquis_localizacao.name = get_encoded_filename(croquis_localizacao)
            certificado_registro2 = request.FILES.get('certificado_registro2')
            certificado_registro2.name = get_encoded_filename(certificado_registro2)
            comprovativo_existência = request.FILES.get('comprovativo_existência')
            comprovativo_existência.name = get_encoded_filename(comprovativo_existência)
            
            empresa.alvara_comercial = alvara_comercial
            empresa.certificado_registro = certificado_registro
            empresa.atestado_sociedade = atestado_sociedade
            empresa.croquis_localizacao = croquis_localizacao
            empresa.certificado_registro2 = certificado_registro2
            empresa.comprovativo_existência = comprovativo_existência

            empresa.save()

            subject = f'Avaliação e Validação dos Documentos | Centro de Formação'
            message = f'A empresa {empresa.nome} de NIF {user.username} enviou os documentos para a verificação da sua conta.'
            sender = EMAIL_HOST_USER
            recipients = [EMAIL_HOST_USER]
            send_mail(subject, message, sender, recipients)

            messages.success(request, 'Documentos enviados com sucesso')
            return render(request, 'views/avaliacao_validacao_view.html', {'notificacoes_n_lidas' : notificacoes_n_lidas})

    return render(request, 'views/avaliacao_validacao_view.html', {'notificacoes_n_lidas' : notificacoes_n_lidas})

@login_required
def ValidarUsuariosView(request):
    notificacoes = Notification.objects.filter(recipient=request.user).order_by('-timestamp')
    notificacoes_n_lidas = notificacoes.filter(unread=True).count()

    eps = Eps.objects.filter(user__is_verified=False)
    sap = Sap.objects.filter(user__is_verified=False)
    centro = Centro.objects.filter(user__is_verified=False)
    psp = Psp.objects.filter(user__is_verified=False)
    dspo = Dspo.objects.filter(user__is_verified=False)


    return render(request, 'views/validar_usuarios_view.html', {'epss': eps, 'saps': sap, 'centros': centro, 'psps': psp, 'dspos': dspo, 'notificacoes_n_lidas' : notificacoes_n_lidas})

@login_required
def atualizar_is_verified(request, sli_id):
    if request.method == 'POST':
        try:
            usuario = CustomUser.objects.get(id=sli_id)
            usuario.is_verified = True
            usuario.save()

            subject = f'VERIFICAÇÃO DA CONTA - SIGESP'
            message = f'A sua conta foi aprovada e já está pronta para exercer as actividades de segurança privada.'
            sender = EMAIL_HOST_USER
            recipients = [usuario.email]
            send_mail(subject, message, sender, recipients)
            notify.send(usuario, recipient=usuario, verb=f"A sua conta foi aprovada e já está pronta para exercer as actividades de segurança privada.")

            return JsonResponse({'message': 'Usuário aprovado com sucesso'}, status=200)
        except CustomUser.DoesNotExist:
            return JsonResponse({'message': 'Usuário não encontrado'}, status=404)
    else:
        return JsonResponse({'message': 'Método de solicitação inválido'}, status=405)
    
@login_required
def EmissaoCarteirasView(request):
    notificacoes = Notification.objects.filter(recipient=request.user).order_by('-timestamp')
    notificacoes_n_lidas = notificacoes.filter(unread=True).count()

    carteiras = CarteiraProfissional.objects.all()

    query = request.GET.get('q', '')
    if query:
        carteiras = CarteiraProfissional.objects.filter(
            Q(nome__icontains=query) |
            Q(bi__icontains=query)
        )
    else:
        carteiras = CarteiraProfissional.objects.all()

    if request.method == 'POST':
        bi = request.POST.get('bi')

        try:
            psp = Psp.objects.get(documento_id=bi)
        except Psp.DoesNotExist:
            messages.error(request, 'Não existe um PSP com esse NIF/BI')
            return render(request, 'views/emissao_carteiras_view.html', {'notificacoes_n_lidas': notificacoes_n_lidas, 'carteiras':carteiras})

        if CarteiraProfissional.objects.filter(bi=bi).exists():
            messages.error(request, 'Já existe uma carteira associada à esse NIF/BI')
            return render(request, 'views/emissao_carteiras_view.html', {'notificacoes_n_lidas': notificacoes_n_lidas, 'carteiras':carteiras})

        nome = psp.nome
        categoria = psp.get_funcao_display()
        dt_registo = psp.user.creation_date
        dt_emissao = datetime.now().strftime('%Y-%m-%d')  # Convertendo para YYYY-MM-DD
        dt_atual = datetime.now()
        ano_validade = dt_atual.year + 3
        data_validade = dt_atual.replace(year=ano_validade).strftime('%Y-%m-%d')  # Convertendo para YYYY-MM-DD
        
        comprovativo_pagamento = request.FILES.get('comprovativo_pagamento')
        comprovativo_pagamento.name = get_encoded_filename(comprovativo_pagamento)
        foto = request.FILES.get('foto')
        foto.name = get_encoded_filename(foto)

        try:
            carteira = CarteiraProfissional(
                autor=psp.user,
                bi=bi,
                nome=nome,
                categoria=categoria,
                dt_registo=dt_registo,
                dt_emissao=dt_emissao,
                dt_validade=data_validade,
                comprovativo_pagamento=comprovativo_pagamento,
                foto=foto
            )
            carteira.save()
            messages.success(request, 'Carteira emitida com sucesso')
        except Exception as e:
            messages.error(request, f'Erro ao emitir a carteira: {e}')

        return render(request, 'views/emissao_carteiras_view.html', {'notificacoes_n_lidas': notificacoes_n_lidas, 'carteiras':carteiras})

    return render(request, 'views/emissao_carteiras_view.html', {'notificacoes_n_lidas': notificacoes_n_lidas, 'carteiras':carteiras})

@login_required
def verificacao_de_carteira(request, token_id):
    carteira = CarteiraProfissional.objects.get(token=token_id)

    return render(request, 'views/verificar_carteira_view.html', {'carteira':carteira})

@login_required
def render_carteira_frente(request, carteira_id):
    carteira = CarteiraProfissional.objects.get(id=carteira_id)

    # Crie um objeto BytesIO para armazenar o PDF
    buffer = BytesIO()

    pdfmetrics.registerFont(TTFont('arial', os.path.join(BASE_DIR, 'templates/static/fonts', 'ARIAL.TTF')))
    pdfmetrics.registerFont(TTFont('arialbd', os.path.join(settings.STATIC_ROOT, 'fonts', 'arialbd.ttf')))
    # Crie um objeto Canvas com o tamanho da página
    c = canvas.Canvas(buffer, pagesize=(85.6,53.98))

    # Desenhe o conteúdo do cartão

    vermelho = '#ff0000'
    amarelo = '#f8b900'
    preto = '#000000'
    c.drawImage(os.path.join(settings.STATIC_ROOT, 'design_carteira', 'logo.jpg'), 5, 40, 8,10)
    c.setFont('arial', 1.8)
    c.drawString(15, 47, "República de Angola")
    #c.drawString(15, 45, "Ministério do Interior")
    c.drawString(15, 45, "Polícia Nacional de Angola")
    c.setFont('arialbd', 2.3)
    c.drawString(15, 42.5, "CARTEIRA DE IDENTIFICAÇÃO PROFISSIONAL")
    azul = '#000e57'
    c.setFillColor(HexColor(azul))
    c.rotate(90)
    c.setFont('arialbd', 1.6)
    c.drawCentredString(24.5, -5, "CARTEIRA DE PROFISSIONAL")
    c.setFillColor(HexColor(preto))

    c.setFont('arialbd', 2)
    c.drawCentredString(24.5, -7, f"{carteira.autor.psp.nuip}")
    c.setFont('arialbd', 1.8)

    c.rotate(-90)

    

    c.setFillColor(HexColor(amarelo))
    x3, y3 = 90.5, 22  # Ponto de partida no canto superior esquerdo
    width3, height3 = 7, 30  # Largura e altura do paralelogramo

    # Calculando os vértices do segundo paralelogramo
    vertices3 = [
        x3, y3,  # Superior esquerdo
        x3 + width3, y3,  # Superior direito
        x3 + width3 - height3, y3 - height3,  # Inferior direito
        x3 - height3, y3 - height3  # Inferior esquerdo
    ]

    drawing3 = Drawing(width=letter[0], height=letter[1])
    paralelogramo3 = Polygon(vertices3, fillColor=amarelo, strokeColor=None)
    drawing3.add(paralelogramo3)
    renderPDF.draw(drawing3, c, 0, 0)

    
    #retangulo
    c.setFillColor(HexColor(amarelo))
    c.rect(0, 0, 100, 5.5, fill=1, stroke=0)
    
    #paralelogramo
    c.rotate(-90)
    x, y = -9, 94  # Ponto de partida no canto superior esquerdo
    width, height = 20, 40  # Largura e altura do paralelogramo
    

    # Calculando os vértices
    vertices = [
        x, y,  # Superior esquerdo
        x + width, y,  # Superior direito
        x + width, y - height,  # Inferior direito
        x, y - height + width  # Inferior esquerdo
    ]

    drawing = Drawing(width=letter[0], height=letter[1])
    paralelogramo = Polygon(vertices, fillColor=vermelho, strokeColor=None)
    drawing.add(paralelogramo)
    renderPDF.draw(drawing, c, 0, 0)

    azul_escuro = '#000b40'
    c.setFillColor(HexColor(azul_escuro))
    c.rotate(90)
    x2, y2 = 90, 20  # Ponto de partida no canto superior esquerdo
    width2, height2 = 7, 30  # Largura e altura do paralelogramo

    # Calculando os vértices do segundo paralelogramo
    vertices2 = [
        x2, y2,  # Superior esquerdo
        x2 + width2, y2,  # Superior direito
        x2 + width2 - height2, y2 - height2,  # Inferior direito
        x2 - height2, y2 - height2  # Inferior esquerdo
    ]

    drawing2 = Drawing(width=letter[0], height=letter[1])
    paralelogramo2 = Polygon(vertices2, fillColor=preto, strokeColor=None)
    drawing2.add(paralelogramo2)
    renderPDF.draw(drawing2, c, 0, 0)

    c.drawImage(os.path.join(settings.MEDIA_ROOT, carteira.foto.name), 16.5,18, 15,20)
    c.drawString(33.5, 36, "NOME:")
    c.drawString(33.5, 28.5, "NIF/BI:")
    c.drawString(33.5, 21, "CATEGORIA:")

    c.setFillColor(HexColor(preto))
    c.drawString(33.5, 33.5, f"{carteira.nome}")
    c.drawString(33.5, 26, f"{carteira.bi}")
    c.drawString(33.5, 18.5, f"{carteira.categoria}")

    c.setStrokeColor(HexColor(vermelho))
    c.setLineWidth(0.5)
    c.rect(55, 25.5, 25, 5.5, fill=0, stroke=1)

    c.setFillColor(HexColor(vermelho))
    c.setFont('arialbd', 2)
    c.drawString(56.35, 27.5, "SEGURANÇA PRIVADA")


    c.setFont('arialbd', 1.8)
    c.setFillColor(HexColor(azul))
    c.drawCentredString(18, 12, "DATA DE REGISTO:")
    c.drawCentredString(41, 12, "DATA DE EMISSÃO:")
    c.drawCentredString(64, 12, "DATA DE VALIDADE:")
    c.setFont('arial', 1.8)
    c.setFillColor(HexColor(preto))

    dt_registo_formatado = carteira.dt_registo.strftime("%d/%m/%Y")
    dt_emissao_formatado = carteira.dt_emissao.strftime("%d/%m/%Y")
    dt_validade_formatado = carteira.dt_validade.strftime("%d/%m/%Y")

    c.drawCentredString(18, 9.5, f"{dt_registo_formatado}")
    c.drawCentredString(41, 9.5, f"{dt_emissao_formatado}")
    c.drawCentredString(64, 9.5, f"{dt_validade_formatado}")

    # Salve o PDF
    c.showPage()
    c.save()

    # Retorne o PDF como parte do conteúdo da resposta HTTP
    pdf = buffer.getvalue()
    buffer.close()
    response = HttpResponse(content_type='application/pdf')
    response.write(pdf)
    return response

@login_required
def render_carteira_verso(request, carteira_id):
    carteira = CarteiraProfissional.objects.get(id=carteira_id)

    # Crie um objeto BytesIO para armazenar o PDF
    buffer = BytesIO()

    pdfmetrics.registerFont(TTFont('arial', os.path.join(BASE_DIR, 'templates/static/fonts', 'ARIAL.TTF')))
    pdfmetrics.registerFont(TTFont('arialbd', os.path.join(settings.STATIC_ROOT, 'fonts', 'arialbd.ttf')))
    # Crie um objeto Canvas com o tamanho da página
    c = canvas.Canvas(buffer, pagesize=(85.6,53.98))

    #desenho do card
    azul = '#000e57'
    amarelo = '#f8b900'
    preto = '#000000'
    vermelho = '#ff0000'

    estilo_personalizado = ParagraphStyle(
        'Custom',
        fontName='arial',
        fontSize=1.8,  # Ajuste o tamanho da fonte conforme necessário
        leading=2,  # Ajuste o espaçamento entre linhas conforme necessário
        alignment=TA_JUSTIFY
    )

    p = Paragraph('Este documento tem por finalidade identificar o Titular desta Carteira na sua qualidade de Profissional de Segurança Privada habilitado nos termos da Lei 10/14 de 30 de Julho, devendo receber e prestar às autoridades policiais todo auxilio que lhe for solicitado em caso de perigo e urgência no exercício das suas funções.', estilo_personalizado)
    p.wrapOn(c, 73,5)
    p.drawOn(c, 6,40)

    p2 = Paragraph('Solicita-se a quem venha encontrar este cartão, o dever de entregar à unidade mais próxima.', estilo_personalizado)
    p2.wrapOn(c, 73,5)
    p2.drawOn(c, 6,34)

    c.setStrokeColor(HexColor(azul))
    c.setLineWidth(0.4)
    c.rect(69, 20, 10, 10, fill=0, stroke=1)

    c.drawImage(os.path.join(settings.MEDIA_ROOT, carteira.qr_code.name), 69.35,20.5, 9.5,9.5)

    c.setFont('arialbd', 2)
    c.setFillColor(HexColor(azul))
    c.drawCentredString(37, 13.5, "O COMANDANTE GERAL DA POLÍCIA NACIONAL")
    

    # Supondo que a largura do canvas seja 85.6 mm
    canvas_width = 73.5
    canvas_height = 17.5

    # Defina a largura da linha e as coordenadas Y
    line_width = 50  # Ajuste conforme necessário
    line_y = canvas_height / 2  # Linha centralizada verticalmente

    # Calcule as coordenadas X para centralizar a linha horizontalmente
    line_x1 = (canvas_width - line_width) / 2
    line_x2 = line_x1 + line_width

    # Defina a espessura da linha (opcional)
    c.setLineWidth(0.15)  # Ajuste a espessura conforme necessário

    # Desenhe a linha horizontal centralizada
    c.line(line_x1, line_y, line_x2, line_y)
    

    
    #design layout
    
    amarelo = '#f8b900'
    c.setFillColor(HexColor(amarelo))
    x3, y3 = 90.5, 22  # Ponto de partida no canto superior esquerdo
    width3, height3 = 7, 30  # Largura e altura do paralelogramo

    # Calculando os vértices do segundo paralelogramo
    vertices3 = [
        x3, y3,  # Superior esquerdo
        x3 + width3, y3,  # Superior direito
        x3 + width3 - height3, y3 - height3,  # Inferior direito
        x3 - height3, y3 - height3  # Inferior esquerdo
    ]

    drawing3 = Drawing(width=letter[0], height=letter[1])
    paralelogramo3 = Polygon(vertices3, fillColor=amarelo, strokeColor=None)
    drawing3.add(paralelogramo3)
    renderPDF.draw(drawing3, c, 0, 0)

    
    #retangulo
    c.setFillColor(HexColor(amarelo))
    c.rect(0, 0, 100, 5.5, fill=1, stroke=0)
    
    #paralelogramo
    c.rotate(-90)
    x, y = -9, 94  # Ponto de partida no canto superior esquerdo
    width, height = 20, 40  # Largura e altura do paralelogramo
    

    # Calculando os vértices
    vertices = [
        x, y,  # Superior esquerdo
        x + width, y,  # Superior direito
        x + width, y - height,  # Inferior direito
        x, y - height + width  # Inferior esquerdo
    ]

    drawing = Drawing(width=letter[0], height=letter[1])
    paralelogramo = Polygon(vertices, fillColor=vermelho, strokeColor=None)
    drawing.add(paralelogramo)
    renderPDF.draw(drawing, c, 0, 0)

    azul_escuro = '#000b40'
    c.setFillColor(HexColor(azul_escuro))
    c.rotate(90)
    x2, y2 = 90, 20  # Ponto de partida no canto superior esquerdo
    width2, height2 = 7, 30  # Largura e altura do paralelogramo

    # Calculando os vértices do segundo paralelogramo
    vertices2 = [
        x2, y2,  # Superior esquerdo
        x2 + width2, y2,  # Superior direito
        x2 + width2 - height2, y2 - height2,  # Inferior direito
        x2 - height2, y2 - height2  # Inferior esquerdo
    ]

    drawing2 = Drawing(width=letter[0], height=letter[1])
    paralelogramo2 = Polygon(vertices2, fillColor=preto, strokeColor=None)
    drawing2.add(paralelogramo2)
    renderPDF.draw(drawing2, c, 0, 0)
    # Salve o PDF
    c.showPage()
    c.save()

    # Retorne o PDF como parte do conteúdo da resposta HTTP
    pdf = buffer.getvalue()
    buffer.close()
    response = HttpResponse(content_type='application/pdf')
    response.write(pdf)
    return response

@login_required
def ServicosView(request):
    notificacoes = Notification.objects.filter(recipient=request.user).order_by('-timestamp')
    notificacoes_n_lidas = notificacoes.filter(unread=True).count()

    context = {
        'notificacoes_n_lidas' : notificacoes_n_lidas
    }

    if request.method == 'POST':
        tipo_pedido = request.POST['tipo_pedido']
        arquivo_enviado = request.FILES.get('ficheiro')
        arquivo_enviado.name = get_encoded_filename(arquivo_enviado)

        entidade = request.user
        
        pedido = Pedido.objects.create(
            entidade=entidade,
            tipo_pedido=tipo_pedido,
            status_pedido='enviado',
            arquivo_enviado=arquivo_enviado,
            data_pedido=timezone.now()
        )
        
        # Enviar e-mail com os detalhes do pedido
        subject = f'Novo Pedido de {tipo_pedido} - #{pedido.id}'
        message = f'Um novo pedido de {tipo_pedido} foi recebido no SIGESP.'
        sender = EMAIL_HOST_USER
        recipients = [EMAIL_HOST_USER]
        send_mail(subject, message, sender, recipients)

        notify.send(request.user, recipient=request.user, verb=f"O seu pedido para emissão de {tipo_pedido} foi enviado com sucesso. Os nossos especialistas irão avaliar o pedido e dar uma resposta o mais breve possível")
        
        messages.success(request, 'Pedido enviado com sucesso.')
        pedidos = Pedido.objects.filter(entidade=request.user)
        context = {
            'notificacoes_n_lidas' : notificacoes_n_lidas,
            'pedidos': pedidos,
        }
        return render(request, 'views/pedidos_view.html', context)    

    return render(request, 'views/servicos_view.html', context)

@login_required
def PedidosView(request):
    notificacoes = Notification.objects.filter(recipient=request.user).order_by('-timestamp')
    notificacoes_n_lidas = notificacoes.filter(unread=True).count()
    
    pedidos = Pedido.objects.filter(entidade=request.user)

    context = {
        'pedidos': pedidos,
        'notificacoes_n_lidas': notificacoes_n_lidas
    }
    return render(request, 'views/pedidos_view.html', context)

@login_required
def PedidoView(request, pedido_id):
    notificacoes = Notification.objects.filter(recipient=request.user).order_by('-timestamp')
    notificacoes_n_lidas = notificacoes.filter(unread=True).count()
    pedido = get_object_or_404(Pedido, id=pedido_id, entidade=request.user)

    context = {
        'pedido': pedido,
        'notificacoes_n_lidas': notificacoes_n_lidas,
    }
    return render(request, 'views/pedido_view.html', context)

@login_required
def RelatoriosView(request):
    notificacoes = Notification.objects.filter(recipient=request.user).order_by('-timestamp')
    notificacoes_n_lidas = notificacoes.filter(unread=True).count()
    relatorios = Relatorio.objects.filter(entidade=request.user)

    context = {
        'notificacoes_n_lidas' : notificacoes_n_lidas,
        'relatorios': relatorios
    }

    if request.method == 'POST':
        tipo_rel = request.POST['tipo_rel']
        arquivo_enviado = request.FILES.get('ficheiro')
        arquivo_enviado.name = get_encoded_filename(arquivo_enviado)

        entidade = request.user
        
        relatorio = Relatorio.objects.create(
            entidade=entidade,
            tipo_rel=tipo_rel,
            status_rel='enviado',
            arquivo_enviado=arquivo_enviado,
            data_rel=timezone.now()
        )
        
        # Enviar e-mail com os detalhes do pedido
        subject = f'Novo Relatório de {tipo_rel} - #{relatorio.id}'
        message = f'Um novo relatório de {tipo_rel} foi recebido no SIGESP.'
        sender = EMAIL_HOST_USER
        recipients = [EMAIL_HOST_USER]
        send_mail(subject, message, sender, recipients)

        notify.send(request.user, recipient=request.user, verb=f"O seu relatório de {tipo_rel} foi enviado com sucesso. Os nossos especialistas irão avaliar o pedido e dar uma resposta o mais breve possível")
        
        messages.success(request, 'Relatório enviado com sucesso.')
        return render(request, 'views/relatorios_view.html', context)    

    return render(request, 'views/relatorios_view.html', context)

@login_required
def RelatorioView(request, rel_id):
    notificacoes = Notification.objects.filter(recipient=request.user).order_by('-timestamp')
    notificacoes_n_lidas = notificacoes.filter(unread=True).count()
    rel = get_object_or_404(Relatorio, id=rel_id, entidade=request.user)

    context = {
        'rel': rel,
        'notificacoes_n_lidas': notificacoes_n_lidas,
    }
    return render(request, 'views/relatorio_view.html', context)

def ConsultarEmpresas(request):

    if request.method == 'POST':
        nif = request.POST['nif']

        empresa = CustomUser.objects.filter(username=nif).first()
        if empresa:
            if empresa.profile_type == 'eps' or empresa.profile_type == 'centro' or empresa.profile_type == 'sap':
                encontrado = 1
                return render(request, 'views/consultar_empresas_view.html', {'empresa':empresa, 'encontrado':encontrado})
        else:
            encontrado = 2
            return render(request, 'views/consultar_empresas_view.html', {'encontrado':encontrado})
        
    return render(request, 'views/consultar_empresas_view.html')

@login_required
def PedidosRecebidosView(request):
    notificacoes = Notification.objects.filter(recipient=request.user).order_by('-timestamp')
    notificacoes_n_lidas = notificacoes.filter(unread=True).count()
    pedidos = Pedido.objects.filter(status_pedido__in=['enviado', 'em_processamento'])
    user = request.user

    context = {
        'pedidos': pedidos,
        'notificacoes_n_lidas': notificacoes_n_lidas
    }

    if request.method == 'POST':
        id_pedido = request.POST.get('id')
        status_pedido = request.POST.get('status_pedido')
        resposta = request.POST.get('resposta')
        arquivo_resposta = request.FILES.get('arquivo_resposta')
        if arquivo_resposta:
            arquivo_resposta.name = get_encoded_filename(arquivo_resposta)

        if id_pedido:
            try:
                pedido = Pedido.objects.get(id=id_pedido)
                if pedido.status_pedido in ['recusado', 'aceite']:
                    messages.error(request, 'Não é possível actualizar um pedido que já foi aceite ou recusado.')
                    return render(request, 'views/pedidos_recebidos_view.html', context)
                else:
                    if status_pedido == 'aceite' and not arquivo_resposta:
                        messages.error(request, 'Não foi possível actualizar o pedido como aceite porque não foi inserido o arquivo de resposta.')
                        return render(request, 'views/pedidos_recebidos_view.html', context)

                    if status_pedido == 'em_processamento' and pedido.status_pedido == 'em_processamento':
                        messages.error(request, 'Este pedido já está em processamento.')
                        return render(request, 'views/pedidos_recebidos_view.html', context)
                    
                    pedido.status_pedido = status_pedido
                    pedido.resposta = resposta
                    pedido.arquivo_resposta = arquivo_resposta
                    pedido.by = user.tecnicodispo.nome
                    pedido.save()

                    status_pedido = pedido.get_status_pedido_display()
                    subject = f'ACTUALIZAÇÃO DE PEDIDO - SIGESP'
                    message = f'O estado do seu pedido de {pedido.tipo_pedido} foi actualizado para [{status_pedido}].'
                    sender = EMAIL_HOST_USER
                    recipients = [pedido.entidade.email]
                    send_mail(subject, message, sender, recipients)

                    notify.send(request.user, recipient=pedido.entidade, verb=f"O estado do seu pedido de {pedido.tipo_pedido} foi actualizado para [{status_pedido}].")
                    
                    log = Logs.objects.create(user=request.user, acao=f'Actualizou o estado do pedido #{pedido.id}')
                    messages.success(request, 'Pedido actualizado')
                    return render(request, 'views/pedidos_recebidos_view.html', context)
                
            except Pedido.DoesNotExist:
                messages.error(request, 'Não existe um pedido com este id.')
        else:
            messages.error(request, 'ID do pedido não fornecido.')

    return render(request, 'views/pedidos_recebidos_view.html', context)

@login_required
def FormacaoView(request):
    notificacoes = Notification.objects.filter(recipient=request.user).order_by('-timestamp')
    notificacoes_n_lidas = notificacoes.filter(unread=True).count()
    formacoes = Formacoes.objects.filter(entidade=request.user)

    context = {
        'notificacoes_n_lidas': notificacoes_n_lidas,
        'formacoes': formacoes
    }

    if request.method == 'POST':
        lista = request.FILES.get('lista')
        lista.name = get_encoded_filename(lista)
        data_inicio = request.POST.get('data_inicio')
        data_fim = request.POST.get('data_fim')

        formacao = Formacoes.objects.create(
            entidade=request.user,
            lista=lista,
            data_abertura=data_inicio,
            data_encerramento=data_fim,
        )

        messages.success(request, 'Formação enviada com sucesso.')
        
    return render(request, 'views/formacao_view.html', context)

@login_required
def MapaPessoalAdmView(request):
    notificacoes = Notification.objects.filter(recipient=request.user).order_by('-timestamp')
    notificacoes_n_lidas = notificacoes.filter(unread=True).count()
    user = request.user

    query = request.GET.get('q', '')
    if query:
        pessoal = MapaPessoal.objects.filter(
            Q(nome__icontains=query) |
            Q(numero_bi__icontains=query)
        )
    else:
        pessoal = MapaPessoal.objects.all()
    

    context = {
        'notificacoes_n_lidas' : notificacoes_n_lidas, 
        'pessoal': pessoal,
        'user': user,
        'query': query,
    }

    return render(request, 'views/mapa_de_pessoal_adm_view.html', context)

@login_required
@require_http_methods(["DELETE"])
def remover_pessoal(request, Id):
    
    pessoa = get_object_or_404(MapaPessoal, pk=Id)
    empresa = pessoa.entidade
    log = Logs.objects.create(user=request.user, acao=f'Removeu um pessoal da empresa {empresa}')
    pessoa.delete()
    
    return JsonResponse({'message': 'Cadastro removido com sucesso.'})

@login_required
def marcar_actividade(request):
    usuario = request.user

    if usuario.profile_type == 'psp':
        uma_semana_atras = timezone.now() - timedelta(days=15)

        if RegistroPonto.objects.filter(usuario=usuario, data_hora__gte=uma_semana_atras).exists():
            messages.error(request, "Você já fez a prova de actividade nos últimos 15 dias.")
        else:
            RegistroPonto.objects.create(usuario=usuario)
            messages.success(request, "Prova de atividade feita com sucesso!")

        return redirect('prova_actividade')

@login_required
def ProvaActividadeView(request):
    notificacoes = Notification.objects.filter(recipient=request.user).order_by('-timestamp')
    notificacoes_n_lidas = notificacoes.filter(unread=True).count()
    query = request.GET.get('nif', '')
    usuarios = CustomUser.objects.all()

    if query:
        usuarios = usuarios.filter(username__icontains=query)

    ultimos_pontos = []

    for usuario in usuarios:
        ultimo_ponto = RegistroPonto.objects.filter(usuario=usuario).order_by('-data_hora').first()
        ultimos_pontos.append({
            'usuario': usuario,
            'ultimo_ponto': ultimo_ponto.data_hora if ultimo_ponto else 'Sem actividade registada'
        })


    context = {
        'notificacoes_n_lidas' : notificacoes_n_lidas, 
        'ultimos_pontos': ultimos_pontos,
        'query': query
    }
    return render(request, 'views/registro_ponto_view.html', context)

@login_required
def minha_carteira(request):
    notificacoes = Notification.objects.filter(recipient=request.user).order_by('-timestamp')
    notificacoes_n_lidas = notificacoes.filter(unread=True).count()

    try:
        carteira = CarteiraProfissional.objects.get(autor=request.user)
        
        if carteira.dt_validade < timezone.now().date():
            notify.send(request.user, recipient=request.user, verb=f"Detectámos que você possui uma carteira expira, ela será automáticamente removida do sistema. Por favor faça uma nova solicitação.")
            carteira.delete()
            messages.error(request, 'A sua carteira encontra-se expirada.')

            return render(request, 'views/minha_carteira_view.html')
        
        context = {
            'notificacoes_n_lidas' : notificacoes_n_lidas,
            'carteira': carteira
        }

        return render(request, 'views/minha_carteira_view.html')
    
    except CarteiraProfissional.DoesNotExist:
        context = {
            'notificacoes_n_lidas' : notificacoes_n_lidas,
        }
        return render(request, 'views/minha_carteira_view.html', context)

@login_required
def MapaArmasAdmView(request):
    notificacoes = Notification.objects.filter(recipient=request.user).order_by('-timestamp')
    notificacoes_n_lidas = notificacoes.filter(unread=True).count()
    user = request.user

    query = request.GET.get('arma', '')
    if query:
        armas = MapaArmas.objects.filter(
            Q(entidade__username__icontains=query) |
            Q(numero_arma__icontains=query)
        )
    else:
        armas = MapaArmas.objects.all()
    

    context = {
        'notificacoes_n_lidas' : notificacoes_n_lidas, 
        'armas': armas,
        'user': user,
        'query': query,
    }

    return render(request, 'views/mapa_de_armas_adm_view.html', context)

@login_required
def EnviarComunicadosView(request):
    notificacoes = Notification.objects.filter(recipient=request.user).order_by('-timestamp')
    notificacoes_n_lidas = notificacoes.filter(unread=True).count()

    context = {
        'notificacoes_n_lidas': notificacoes_n_lidas,
    }

    if request.method == 'POST':
        tipo = request.POST.get('tipo')
        para = request.POST.get('para')
        mensagem = request.POST.get('mensagem')

        if tipo == '':
            messages.error(request, "Insira o tipo de comunicado")
            return render(request, 'views/comunicados_view.html', context)


        if tipo == 'geral':
            usuarios = CustomUser.objects.filter(
                is_verified=True,
                profile_type__in=['eps', 'sap', 'centro', 'psp']
            )
        elif tipo == 'especifico':
            if para == '':
                messages.error(request, "Insira o destinatário")
                return render(request, 'views/comunicados_view.html', context)
        
            if para == 'eps':
                usuarios = CustomUser.objects.filter(profile_type='eps', is_verified=True)
            elif para == 'sap':
                usuarios = CustomUser.objects.filter(profile_type='sap', is_verified=True)
            elif para == 'centro':
                usuarios = CustomUser.objects.filter(profile_type='centro', is_verified=True)
            elif para == 'psp':
                usuarios = CustomUser.objects.filter(profile_type='psp', is_verified=True)
            else:
                usuarios = []

        if mensagem == '':
            messages.error(request, "Insira a mensagem")
            return render(request, 'views/comunicados_view.html', context)

        for user in usuarios:
            notify.send(request.user, recipient=user, verb=mensagem)

        messages.success(request, "Comunicado enviado com sucesso!")
        return render(request, 'views/comunicados_view.html', context)
    return render(request, 'views/comunicados_view.html', context)

@login_required
def ListaEnvolvidosCrimesView(request):
    notificacoes = Notification.objects.filter(recipient=request.user).order_by('-timestamp')
    notificacoes_n_lidas = notificacoes.filter(unread=True).count()
    user = request.user

    query = request.GET.get('q', '')
    if query:
        acusados = ListaEnvolvidosCrime.objects.filter(
            Q(acusado__username__icontains=query) |
            Q(acusado__psp__nome__icontains=query)
        )
    else:
        acusados = ListaEnvolvidosCrime.objects.all()

    context = {
        'notificacoes_n_lidas' : notificacoes_n_lidas, 
        'acusados': acusados,
        'query': query,
    }

    if request.method == 'POST':
        bi = request.POST['bi']

        try:
            acusado = CustomUser.objects.get(username=bi)
            psp = Psp.objects.get(user=acusado)

            assunto = request.POST['assunto']

            if assunto == '':
                messages.error(request, 'Insira o tipo de crime.')
                return render(request, 'views/lista_envolvidos_view.html', context)
            
            crime = ListaEnvolvidosCrime.objects.create(
                acusado=acusado,
                assunto=assunto,
                autor=request.user
            )
            messages.success(request, 'Cadastro feito com sucesso.')
            return render(request, 'views/lista_envolvidos_view.html', context)


        except (CustomUser.DoesNotExist, Psp.DoesNotExist):
            messages.error(request, 'Profissional não encontrado.')
            return render(request, 'views/lista_envolvidos_view.html', context)
    
    
    return render(request, 'views/lista_envolvidos_view.html', context)


def RelatoriosProvinciaisView(request):
    notificacoes = Notification.objects.filter(recipient=request.user).order_by('-timestamp')
    notificacoes_n_lidas = notificacoes.filter(unread=True).count()
    user = request.user

    query = request.GET.get('q', '')
    if query:
        rels = EmissaoRelatorios.objects.filter(
            Q(provincia__icontains=query) |
            Q(autor__username__icontains=query)
        )
    else:
        rels = EmissaoRelatorios.objects.all()

    context = {
        'notificacoes_n_lidas' : notificacoes_n_lidas, 
        'rels': rels,
        'query': query,
    }

    return render(request, 'views/relatorios_provinciais_view.html', context)

def MultasProvinciaisView(request):
    notificacoes = Notification.objects.filter(recipient=request.user).order_by('-timestamp')
    notificacoes_n_lidas = notificacoes.filter(unread=True).count()
    user = request.user

    query = request.GET.get('q', '')
    if query:
        muls = EmissaoMultas.objects.filter(
            Q(provincia__icontains=query) |
            Q(autor__username__icontains=query)
        )
    else:
        muls = EmissaoMultas.objects.all()

    context = {
        'notificacoes_n_lidas' : notificacoes_n_lidas, 
        'muls': muls,
        'query': query,
    }

    return render(request, 'views/multas_provinciais_view.html', context)
