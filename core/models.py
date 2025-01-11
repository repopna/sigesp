from django.utils import timezone
from django.db import models
from contas.models import CustomUser
import qrcode
from io import BytesIO
from django.core.files import File
import uuid
from datetime import timedelta
from django.utils import timezone

# Create your models here.

def curriculum_upload_to(instance, filename):
    return f'Solicitacao_licencas/{instance.autor.username}/curriculum_vitae/{filename}'
def certificado_upload_to(instance, filename):
    return f'Solicitacao_licencas/{instance.autor.username}/certificado/{filename}'
def copia_bi_upload_to(instance, filename):
    return f'Solicitacao_licencas/{instance.autor.username}/copia_bi/{filename}'
def registro_criminal_upload_to(instance, filename):
    return f'Solicitacao_licencas/{instance.autor.username}/regsitro_criminal/{filename}'
def comprovativo_upload_to(instance, filename):
    return f'Solicitacao_licencas/{instance.autor.username}/comprovativo/{filename}'

class SolicitacaoLicenca(models.Model):
    autor = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    categoria = models.CharField('Categoria a requerer',choices=[
        ('director_s','Director de Segurança'),('coordenador_s','Coordenador de Segurança'),
        ('supervisor_s','Supervisor de Segurança'),('rondante','Rondante'),
        ('vig_principal','Vigilante Principal'),('vig_porteiro','Vig. Porteiro'),
        ('vig_transporte','Vig. Transporte de Valores - VTV'),('vig_proteccao','Vig. de Protecção e Acompanhamento Pessoal - VPAP'),
        ('vig_fiscal','Vig. Fiscal de Transportes Públicos- VFTP'),('assistente_desp','Assistente de Recinto Desportivo - ARD'),
        ('assistente_esp','Assistente de Recinto de Espetáculo- ARE'),('operador_cctv','Operador de CCTV'),
        ('operador_sistema','Operador de Sistema de Alarme'),('armeiro','Armeiro'),
        ('gestor_a','Gestor do Armeiro'),('formador','Formador de Segurança Privada'),
        ('instrutor','Instrutor de Tiro')
    ], max_length=50)
    motivo = models.CharField('Motivo', choices=[
        ('furto','Furto ou Roubo'),('extravio','Extravio'),
        ('danificado','Danificado'),('alteracao','Alteração da Categoria')
    ], max_length=50)
    pedido = models.CharField('Pedido', choices=[
        ('novo','Novo'), ('renovacao','Renovação'),
        ('via2','2ª Via')], max_length=50)
    certificado = models.FileField('Certificado de Formações Concluídas', upload_to=curriculum_upload_to)
    copia_bi = models.FileField('Cópia do Bilhete', upload_to=copia_bi_upload_to)
    registro_criminal = models.FileField('Registro Criminal', upload_to=registro_criminal_upload_to)
    curriculum_vitae = models.FileField('Curriculum Vitae', upload_to=curriculum_upload_to)
    comprovativo = models.FileField('Comprovativo de Serviço Militar Obrigatório', upload_to=comprovativo_upload_to)
    

    class Meta:
        verbose_name = 'Solicitação de Licença'
        verbose_name_plural = 'Solicitações de Licenças'
    
    def __str__(self):
        return f'{self.id} - {self.autor.username}'
    
class MapaArmas(models.Model):
    entidade = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    numero_arma = models.CharField('Número da Arma', max_length=100)
    classificacao = models.CharField('Classificação', choices=[('caca','Caça'),('defesa','Defesa'),('recreio','Recreio')], max_length=10, default='caca')
    marca = models.CharField('Marca da Arma', max_length=100)
    origem = models.CharField('Origem da Arma', max_length=100)
    calibre = models.CharField('Calibre da Arma', max_length=100)
    cano = models.CharField('Número de Cano da Arma', max_length=100)
    tiro = models.CharField('Tiros da Arma', max_length=100)
    comprimento_cano = models.CharField('Comprimento do Cano da Arma', max_length=100)
    alma = models.CharField('Alma da Arma', max_length=100)
    percussao = models.CharField('Percussão da Arma', max_length=100)
    culatra = models.CharField('Culatra da Arma', max_length=100)
    caes = models.CharField('Cães', choices=[('com','Com'),('sem','Sem')], max_length=10, default='sem')
    platinas = models.CharField('Platinas', choices=[('com','Com'),('sem','Sem')], max_length=10, default='sem')
    data_registro = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Mapa de Armas'
        verbose_name_plural = 'Mapa de Armas'

    
    def __str__(self):
        return f'Arma #{self.id} - {self.entidade} - {self.numero_arma}'
    
class MapaPessoal(models.Model):
    entidade = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    nome = models.CharField('Nome', max_length=100)
    sexo = models.CharField('Sexo', choices=[('M','Masculino'), ('F','Femenino')], max_length=100, null=True)
    estado_civil = models.CharField('Estado Civil', choices=[('solteiro','Solteiro(a)'),('casado','Casado(a)'),('divorciado','Divorciado(a)'),
        ('viuvo','Viúvo(a)')], max_length=50, blank=True, null=True)
    funcao = models.CharField('função', max_length=100, null=True)
    numero_bi = models.CharField('Número do Bi', max_length=100)
    data_nascimento = models.DateField('Data de Nascimento')
    tempo_servico = models.DateField('Tempo de Serviço')
    data_registro = models.DateTimeField('Data', default=timezone.now)

    class Meta:
        verbose_name = 'Mapa de Pessoal'
        verbose_name_plural = 'Mapa de Pessoal'

    def __str__(self):
        return f'Pessoal #{self.id} - {self.entidade} - {self.nome}'
    
def ficheiro_upload_to(instance, filename):
    return f'mapa_postos/{instance.entidade.username}/{filename}'

class MapaPostos(models.Model):
    entidade = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    ficheiro = models.FileField('Ficheiro', upload_to=ficheiro_upload_to)
    data_registro = models.DateTimeField('Data', default=timezone.now)


    class Meta:
        verbose_name = 'Mapa de Postos'
        verbose_name_plural = 'Mapa de Postos'

    def __str__(self):
        return f'Pessoal #{self.id} - {self.entidade}'

def multa_upload_to(instance, filename):
    data_formatada = instance.data_de_envio.strftime('%d%m%Y')
    return f'relatorios/{data_formatada}/{filename}'

class EmissaoMultas(models.Model):
    autor = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    ficheiro = models.FileField('Arquivo', upload_to=multa_upload_to)
    provincia = models.CharField('Provincia', max_length=50)
    data_de_envio = models.DateField('Data de Envio', default=timezone.now)

    class Meta:
        verbose_name = 'Multa'
        verbose_name_plural = 'Multas dos Técnicos Provinciais'

    def __str__(self):
        return f'Multa #{self.id} - {self.autor.dspo.nome}'

def relatorio_upload_to(instance, filename):
    data_formatada = instance.data_de_envio.strftime('%d%m%Y')
    return f'relatorios/{data_formatada}/{filename}'

class EmissaoRelatorios(models.Model):
    autor = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    ficheiro = models.FileField('Arquivo', upload_to=relatorio_upload_to)
    provincia = models.CharField('Provincia', max_length=50)
    data_de_envio = models.DateField('Data de Envio', default=timezone.now)

    class Meta:
        verbose_name = 'Relatório'
        verbose_name_plural = 'Relatórios dos Técnicos Provinciais'

    def __str__(self):
        return f'#{self.id} Relatório de {self.data_de_envio} - {self.autor.dspo.nome}'
    
class Denuncias(models.Model):
    autor = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    tipo_de_denuncia = models.CharField('Tipo de Denúncia', choices=[('geral','Geral'),('pessoal','Pessoal')], max_length=50, blank=True)
    acusado = models.CharField('Acusado', max_length=100, blank=True, null=True)
    descricao = models.CharField('Descrição', max_length=500)
    data_da_denuncia = models.DateField('Data da Denúncia', default=timezone.now)

    class Meta:
        verbose_name = 'Denúncia'
        verbose_name_plural = 'Denúncias'

    def __str__(self):
        return f'Comunicação #{self.id} | {self.autor}'
    
def foto_upload_to(instance, filename):
    return f'carteiras/{instance.autor.username}/foto/{filename}'

def comprovativo_upload_to(instance, filename):
    return f'carteiras/{instance.autor.username}/comprovativo/{filename}'

def qr_upload_to(instance, filename):
    return f'carteiras/{instance.autor.username}/qr_code/{filename}'

class CarteiraProfissional(models.Model):
    autor = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    nome = models.CharField('Nome', max_length=100)
    foto = models.ImageField('Foto', upload_to=foto_upload_to, blank=True, null=True)
    bi = models.CharField('NIF/BI', max_length=100)
    categoria = models.CharField('Categoria', max_length=100)
    dt_registo = models.DateField('Data de Registo')
    dt_emissao = models.DateField('Data de Emissão', default=timezone.now)
    dt_validade = models.DateField('Data de Validade')
    comprovativo_pagamento = models.FileField('Comprovativo de Pagamento',upload_to=comprovativo_upload_to, blank=True, null=True)
    banned = models.BooleanField('Ban', default=False)
    qr_code = models.ImageField('QR CODE', upload_to=qr_upload_to, blank=True, null=True)
    token = models.CharField(max_length=100, unique=True, editable=False, default=uuid.uuid4)

    def save(self, *args, **kwargs):
        # Gera o token se não existir
        if not self.token:
            self.token = str(uuid.uuid4())

        # Chama o método save da classe base
        super().save(*args, **kwargs)

        # Gera o conteúdo do QR code
        base_url = 'https://sigesp2.kirene.ao/verificacao-de-carteira/'
        verificacao_url = f'{base_url}{self.token}'
        qr_content = f'{verificacao_url}'

        # Gera o QR code
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(qr_content)
        qr.make(fit=True)

        # Cria uma imagem do QR code
        img = qr.make_image(fill='black', back_color='white')

        # Salva a imagem do QR code no campo qr_code
        buffer = BytesIO()
        img.save(buffer, format='PNG')
        self.qr_code.save(f'{self.bi}_qrcode.png', File(buffer), save=False)

        # Chama o método save da classe base novamente para salvar o QR code
        super().save(*args, **kwargs)

def arquivo_enviado_upload_to(instance, filename):
    return f'Pedidos/{instance.entidade}/{instance.id}/arquivo_envidado/{filename}'

def arquivo_resposta_upload_to(instance, filename):
    return f'Pedidos/{instance.entidade}/{instance.id}/arquivo_resposta/{filename}'
    
class Pedido(models.Model):
    STATUS_CHOICES = [
        ('enviado', 'Enviado'),
        ('em_processamento', 'Em Processamento'),
        ('recusado', 'Recusado'),
        ('aceite', 'Aceite')
    ]
    
    entidade = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    tipo_pedido = models.CharField('Pedido', max_length=255)
    status_pedido = models.CharField(max_length=20, choices=STATUS_CHOICES)
    resposta = models.TextField('Resposta (Opcional)', blank=True, null=True)
    arquivo_enviado = models.FileField('Arquivo Enviado', upload_to=arquivo_enviado_upload_to)
    arquivo_resposta = models.FileField('Arquivo de Resposta', upload_to=arquivo_resposta_upload_to, blank=True, null=True)
    by = models.CharField('byy', max_length=255, default='', null=True)
    data_pedido = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = 'Pedidos'

    
    def __str__(self):
        return f'Pedido #{self.id} - {self.entidade} - {self.tipo_pedido}'

def arquivo_rel_enviado_upload_to(instance, filename):
    return f'relatorio/{instance.entidade}/{instance.id}/arquivo_enviado/{filename}'

def arquivo_rel_resposta_upload_to(instance, filename):
    return f'relatorio/{instance.entidade}/{instance.id}/arquivo_resposta/{filename}'

class Relatorio(models.Model):
    STATUS_CHOICES = [
        ('enviado', 'Enviado'),
        ('em_processamento', 'Em Processamento'),
        ('recusado', 'Recusado'),
        ('aceite', 'Aceite')
    ]
    
    entidade = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    tipo_rel = models.CharField('Tipo de Relatório', max_length=255)
    status_rel = models.CharField(max_length=20, choices=STATUS_CHOICES)
    resposta = models.TextField('Resposta (Opcional)', blank=True, null=True)
    arquivo_enviado = models.FileField('Arquivo Enviado', upload_to=arquivo_rel_enviado_upload_to)
    arquivo_resposta = models.FileField('Arquivo de Resposta', upload_to=arquivo_rel_resposta_upload_to, blank=True, null=True)
    data_rel = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = 'Relatórios'
    
    def __str__(self):
        return f'Relatório #{self.id} - {self.entidade}'
    
def arquivo_forma_upload_to(instance, filename):
    return f'formacao/lista_candidatos/{instance.entidade}/{filename}'

class Formacoes(models.Model):
    entidade = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    lista = models.FileField('Arquivo de Resposta', upload_to=arquivo_forma_upload_to, blank=True, null=True)
    data_abertura = models.DateField()
    data_encerramento = models.DateField()
    data_cadastro = models.DateTimeField(default=timezone.now)

    class Meta:
        verbose_name_plural = 'Formações'
    
    def __str__(self):
        return f'{self.entidade}'

class RegistroPonto(models.Model):
    usuario = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    data_hora = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"{self.usuario.username} - {self.data_hora}"
    

class ListaEnvolvidosCrime(models.Model):
    ASSUNTO_CHOICES = [
        ('roubo', 'Roubo'),
        ('furto', 'Furto'),
        ('assalto', 'Assalto')
    ]
    acusado = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    assunto = models.CharField(max_length=100, choices=ASSUNTO_CHOICES)
    autor = models.CharField(max_length=100, default='')
    data = models.DateTimeField(default=timezone.now)
    

