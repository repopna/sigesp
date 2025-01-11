from datetime import timedelta
import uuid
from django.utils import timezone
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.contrib.sessions.models import Session

# Create your models here.
class CustomUser(AbstractUser):
    telefone = models.CharField('Telefone', max_length=100)
    profile_type = models.CharField('Perfil' , max_length=50, choices=[('psimed', 'Psicólogo / Médico'), ('eps', 'Empresa Privada de Segurança'), ('sap', 'Sistema de Auto Proteção'), ('centro', 'Centro de Formação'), ('emso', 'EMSO'), ('psp', 'Profissional de Segurança Privada'), ('dspo','DSPO/CMDO PROVINCIAL'), ('tecdsp', 'Especialista da DISPO')], blank=True, null=True)
    is_verified = models.BooleanField('Verificado', default=False)
    creation_date = models.DateTimeField('Data de Criação', default=timezone.now)

def comprovativos_upload_to(instance, filename):
    return f'comprovativos/{instance.user.username}/{filename}'

class Licenca(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    contato = models.CharField(max_length=100, blank=True)
    comprovativo_pagamento = models.FileField(upload_to=comprovativos_upload_to, blank=True, null=True)
    token = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    valid_until = models.DateTimeField()
    current_session_key = models.CharField(max_length=40, blank=True, null=True)

    def save(self, *args, **kwargs):
        if not self.id:
            self.valid_until = timezone.now().date() + timedelta(days=365)
        super().save(*args, **kwargs)

    def is_valid(self):
        return self.valid_until > timezone.now()
    
    def dias_restantes(self):
        agora = timezone.now()
        if self.valid_until > agora:
            return (self.valid_until - agora).days
        return 0
    
    def logout_previous_session(self):
        if self.current_session_key:
            try:
                session = Session.objects.get(session_key=self.current_session_key)
                session.delete()
            except Session.DoesNotExist:
                pass
    
    def __str__(self):
        return f"{self.user.username} ({self.token})"

# perfil eps

def eps_copia_licenca_upload_to(instance, filename):
    return f'eps/{instance.nif}/copia_licenca/{filename}'

def eps_certidao_upload_to(instance, filename):
    return f'eps/{instance.nif}/certidao/{filename}'

def eps_copia_bi_sg_upload_to(instance, filename):
    return f'eps/{instance.nif}/copia_bi_sg/{filename}'

def eps_foto_passe_sg_upload_to(instance, filename):
    return f'eps/{instance.nif}/foto_passe_sg/{filename}'

def alvara_comercial_upload_to(instance, filename):
    return f'eps/{instance.nif}/alvara_comercial/{filename}'

def certificado_registro_upload_to(instance, filename):
    return f'eps/{instance.nif}/certificado_registro/{filename}'

def atestado_sociedade_upload_to(instance, filename):
    return f'eps/{instance.nif}/atestado_sociedade/{filename}'

def croquis_localizacao_upload_to(instance, filename):
    return f'eps/{instance.nif}/croquis_localizacao/{filename}'

def certificado_registro2_upload_to(instance, filename):
    return f'eps/{instance.nif}/certificado_registro2/{filename}'

def comprovativo_existência_upload_to(instance, filename):
    return f'eps/{instance.nif}/comprovativo_existência/{filename}'

class Eps(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE)
    nif = models.CharField('NIF', max_length=100, blank=True, null=True)
    nome = models.CharField('Nome da Instituição', max_length=100, blank=True, null=True)
    morada = models.CharField('Morada', max_length=100, blank=True, null=True)
    provincia = models.CharField('Província', max_length=100, blank=True, null=True)

    # o prefixo sg significa (socio / gerente)
    sg_nome = models.CharField('Nome Completo do Sócio / Gerente', max_length=100, blank=True, null=True)
    sg_funcao = models.CharField('Funçao do Sócio / Gerente', max_length=100, blank=True, null=True)
    sg_id = models.CharField('NIF / BIº do Sócio / Gerente', max_length=100, blank=True, null=True)
    sg_morada = models.CharField('Morada do Sócio / Gerente', max_length=100, blank=True, null=True)
    sg_email = models.CharField('Email do Sócio / Gerente', max_length=100, blank=True, null=True)
    sg_telefone = models.CharField('Telefone do Sócio / Gerente', max_length=100, blank=True, null=True)
    copia_licenca = models.FileField('Cópia da Liecença', upload_to=eps_copia_licenca_upload_to)
    certidao = models.FileField('Certidão da Empresa', upload_to=eps_certidao_upload_to)
    copia_bi_sg = models.FileField('Cópia do BI do Sócio/Gerente', upload_to=eps_copia_bi_sg_upload_to)
    foto_passe_sg = models.FileField('Foto Passe do Sócio/Gerente', upload_to=eps_foto_passe_sg_upload_to)
    
    # pós cadastro
    alvara_comercial = models.FileField('Alvará Comercial', upload_to=alvara_comercial_upload_to, blank=True, null=True)
    certificado_registro = models.FileField('Certificado de Registo Estático', upload_to=certificado_registro_upload_to, blank=True, null=True)
    atestado_sociedade = models.FileField('Atestado da Sociedade Comercial', upload_to=atestado_sociedade_upload_to, blank=True, null=True)
    croquis_localizacao = models.FileField('Cróquis de Localização da Sede da Empresa', upload_to=croquis_localizacao_upload_to, blank=True)
    certificado_registro2 = models.FileField('Certificado de Registo Comercial', upload_to=certificado_registro2_upload_to, blank=True, null=True)
    comprovativo_existência = models.FileField('Comprovatico de Existência de Instalação', upload_to=comprovativo_existência_upload_to, blank=True, null=True)
    
    class Meta:
        verbose_name = 'EPS'
        verbose_name_plural = 'EPS'
    
    def __str__(self):
        return self.nif
    

# perfil centro

def centro_copia_licenca_upload_to(instance, filename):
    return f'centro/{instance.nif}/copia_licenca/{filename}'

def centro_certidao_upload_to(instance, filename):
    return f'centro/{instance.nif}/certidao/{filename}'

def centro_copia_bi_sg_upload_to(instance, filename):
    return f'centro/{instance.nif}/copia_bi_sg/{filename}'

def centro_foto_passe_sg_upload_to(instance, filename):
    return f'centro/{instance.nif}/foto_passe_sg/{filename}'

def centro_alvara_comercial_upload_to(instance, filename):
    return f'centro/{instance.nif}/alvara_comercial/{filename}'

def centro_certificado_registro_upload_to(instance, filename):
    return f'centro/{instance.nif}/certificado_registro/{filename}'

def centro_atestado_sociedade_upload_to(instance, filename):
    return f'centro/{instance.nif}/atestado_sociedade/{filename}'

def centro_croquis_localizacao_upload_to(instance, filename):
    return f'centro/{instance.nif}/croquis_localizacao/{filename}'

def centro_certificado_registro2_upload_to(instance, filename):
    return f'centro/{instance.nif}/certificado_registro2/{filename}'

def centro_comprovativo_existência_upload_to(instance, filename):
    return f'centro/{instance.nif}/comprovativo_existência/{filename}'
    
class Centro(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE)
    nif = models.CharField('NIF', max_length=100, blank=True, null=True)
    nome = models.CharField('Nome da Instituição', max_length=100, blank=True, null=True)
    morada = models.CharField('Morada', max_length=100, blank=True, null=True)
    provincia = models.CharField('Província', max_length=100, blank=True, null=True)


    # o prefixo sg significa (socio / gerente)
    sg_nome = models.CharField('Nome Completo do Sócio / Gerente', max_length=100, blank=True, null=True)
    sg_funcao = models.CharField('Funçao do Sócio / Gerente', max_length=100, blank=True, null=True)
    sg_id = models.CharField('NIF / BIº do Sócio / Gerente', max_length=100, blank=True, null=True)
    sg_morada = models.CharField('Morada do Sócio / Gerente', max_length=100, blank=True, null=True)
    sg_email = models.CharField('Email do Sócio / Gerente', max_length=100, blank=True, null=True)
    sg_telefone = models.CharField('Telefone do Sócio / Gerente', max_length=100, blank=True, null=True)
    copia_licenca = models.FileField('Cópia da Liecença', upload_to=centro_copia_licenca_upload_to)
    certidao = models.FileField('Certidão da Empresa', upload_to=centro_certidao_upload_to)
    copia_bi_sg = models.FileField('Cópia do BI do Sócio/Gerente', upload_to=centro_copia_bi_sg_upload_to)
    foto_passe_sg = models.FileField('Foto Passe do Sócio/Gerente', upload_to=centro_foto_passe_sg_upload_to)

    # pós cadastro
    alvara_comercial = models.FileField('Alvará Comercial', upload_to=centro_alvara_comercial_upload_to, blank=True, null=True)
    certificado_registro = models.FileField('Certificado de Registo Estático', upload_to=centro_certificado_registro_upload_to, blank=True, null=True)
    atestado_sociedade = models.FileField('Atestado da Sociedade Comercial', upload_to=centro_atestado_sociedade_upload_to, blank=True, null=True)
    croquis_localizacao = models.FileField('Cróquis de Localização da Sede da Empresa', upload_to=centro_croquis_localizacao_upload_to, blank=True)
    certificado_registro2 = models.FileField('Certificado de Registo Comercial', upload_to=centro_certificado_registro2_upload_to, blank=True, null=True)
    comprovativo_existência = models.FileField('Comprovatico de Existência de Instalação', upload_to=centro_comprovativo_existência_upload_to, blank=True, null=True)
    
    class Meta:
        verbose_name = 'Centros de Formação'
        verbose_name_plural = 'Centros de Formação'
    
    def __str__(self):
        return self.nif

# perfil sap

def sap_copia_licenca_upload_to(instance, filename):
    return f'sap/{instance.nif}/copia_licenca/{filename}'

def sap_certidao_upload_to(instance, filename):
    return f'sap/{instance.nif}/certidao/{filename}'

def sap_copia_bi_sg_upload_to(instance, filename):
    return f'sap/{instance.nif}/copia_bi_sg/{filename}'

def sap_foto_passe_sg_upload_to(instance, filename):
    return f'sap/{instance.nif}/foto_passe_sg/{filename}'

def sap_alvara_comercial_upload_to(instance, filename):
    return f'eps/{instance.nif}/alvara_comercial/{filename}'

def sap_certificado_registro_upload_to(instance, filename):
    return f'sap/{instance.nif}/certificado_registro/{filename}'

def sap_atestado_sociedade_upload_to(instance, filename):
    return f'sap/{instance.nif}/atestado_sociedade/{filename}'

def sap_croquis_localizacao_upload_to(instance, filename):
    return f'sap/{instance.nif}/croquis_localizacao/{filename}'

def sap_certificado_registro2_upload_to(instance, filename):
    return f'sap/{instance.nif}/certificado_registro2/{filename}'

def sap_comprovativo_existência_upload_to(instance, filename):
    return f'sap/{instance.nif}/comprovativo_existência/{filename}'

class Sap(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE)
    nif = models.CharField('NIF', max_length=100, blank=True, null=True)
    nome = models.CharField('Nome da Instituição', max_length=100, blank=True, null=True)
    morada = models.CharField('Morada', max_length=100, blank=True, null=True)
    provincia = models.CharField('Província', max_length=100, blank=True, null=True)

    # o prefixo sg significa (socio / gerente)
    sg_nome = models.CharField('Nome Completo do Sócio / Gerente', max_length=100, blank=True, null=True)
    sg_funcao = models.CharField('Funçao do Sócio / Gerente', max_length=100, blank=True, null=True)
    sg_id = models.CharField('NIF / BIº do Sócio / Gerente', max_length=100, blank=True, null=True)
    sg_morada = models.CharField('Morada do Sócio / Gerente', max_length=100, blank=True, null=True)
    sg_email = models.CharField('Email do Sócio / Gerente', max_length=100, blank=True, null=True)
    sg_telefone = models.CharField('Telefone do Sócio / Gerente', max_length=100, blank=True, null=True)
    copia_licenca = models.FileField('Cópia da Liecença', upload_to=sap_copia_licenca_upload_to)
    certidao = models.FileField('Certidão da Empresa', upload_to=sap_certidao_upload_to)
    copia_bi_sg = models.FileField('Cópia do BI do Sócio/Gerente', upload_to=sap_copia_bi_sg_upload_to)
    foto_passe_sg = models.FileField('Foto Passe do Sócio/Gerente', upload_to=sap_foto_passe_sg_upload_to)

    # pós cadastro
    alvara_comercial = models.FileField('Alvará Comercial', upload_to=sap_alvara_comercial_upload_to, blank=True, null=True)
    certificado_registro = models.FileField('Certificado de Registo Estático', upload_to=sap_certificado_registro_upload_to, blank=True, null=True)
    atestado_sociedade = models.FileField('Atestado da Sociedade Comercial', upload_to=sap_atestado_sociedade_upload_to, blank=True, null=True)
    croquis_localizacao = models.FileField('Cróquis de Localização da Sede da Empresa', upload_to=sap_croquis_localizacao_upload_to, blank=True, null=True)
    certificado_registro2 = models.FileField('Certificado de Regist0 Comercial', upload_to=sap_certificado_registro2_upload_to, blank=True, null=True)
    comprovativo_existência = models.FileField('Comprovatico de Existência de Instalação', upload_to=sap_comprovativo_existência_upload_to, blank=True, null=True)
    
    class Meta:
        verbose_name = 'SAP'
        verbose_name_plural = 'SAP'
    
    def __str__(self):
        return self.nif

def psp_declaracao_servico_upload_to(instance, filename):
    return f'psp/{instance.documento_id}/declaracao_servico/{filename}'

def psp_foto_passe_upload_to(instance, filename):
    return f'psp/{instance.documento_id}/foto_passe/{filename}'

def psp_documento_id_upload_to(instance, filename):
    return f'psp/{instance.documento_id}/documento_id/{filename}'

def psp_agregado_familiar_upload_to(instance, filename):
    return f'psp/{instance.documento_id}/agregado_familiar/{filename}'
    
class Psp(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE)
    ANO_ATUAL = timezone.now().year
    nome = models.CharField('Nome Completo', max_length=100, blank=True, null=True)
    nuip = models.CharField('NUIP', max_length=50, unique=True, null=True)
    estado_civil = models.CharField('Estado Civil', choices=[('solteiro','Solteiro(a)'),('casado','Casado(a)'),('divorciado','Divorciado(a)'),
        ('viuvo','Viúvo(a)')], max_length=50, blank=True, null=True)
    agregado_familiar = models.FileField('Agregado Familiar', upload_to=psp_agregado_familiar_upload_to, blank=True, null=True)
    funcao = models.CharField('Função', choices=[('DS','Director de Segurança'), ('CS','Coordenador de Segurança'),
        ('R','Rondante'), ('V','Vigilante'), ('FSP','Formador de Segurança Privada'), ('IT','Instrutor de Tiro'), 
        ('CSG','Consultor de Segurança'), ('A','Armeiro'), ('GA','Gestor do Armeiro'), ('SS','Supervisor de Segurança'),
        ('GME','Gestor de Meios e Equipamentos'), ('AME','Armazenista de Meios e Equipamentos'), 
        ('MAD','Mecânico de Armas e Defesas')] , max_length=50, blank=True, null=True)
    sub_funcao = models.CharField('Sub Função', choices=[('vig_principal','Vigilante Principal'), ('vig_porteiro','Vig. Porteiro'),
        ('vig_transporte','Vig. Transporte de Valores - VTV'), ('vig_proteccao','Vig. de Protecção e Acompanhamento Pessoal - VPAP'),
        ('vig_fiscal','Vig. Fiscal de Transportes Públicos- VFTP'), ('assistente_desp','Assistente de Recinto Desportivo - ARD'), 
        ('assistente_esp','Assistente de Recinto de Espetáculo- ARE'), ('operador_cctv','Operador de CCTV'), 
        ('operador_sistema','Operador de Sistema de Alarme'), ] , max_length=50, blank=True, null=True)
    documento = models.CharField('Documento Pessoal', choices=[('bi','Nº Bilhete de Identidade'), ('passaporte','Nº Passaporte'),
        ('c_residente','Cartão de Residente')] , max_length=50, blank=True, null=True)
    documento_id = models.CharField('Número do Documento', max_length=100, blank=True, null=True)
    vinculo = models.BooleanField('Vínculo Empresarial')
    nome_empresa = models.CharField('Nome da Empresa', max_length=100, blank=True, null=True)
    funcao_empresa = models.CharField('Função na Empresa', max_length=100, blank=True, null=True)
    prof_independente = models.BooleanField('Profissional Independente')
    morada = models.CharField('Morada', max_length=100, blank=True, null=True)
    declaracao_servico = models.FileField('Declaração do Serviço', upload_to=psp_declaracao_servico_upload_to)
    foto_passe = models.FileField('Foto Passe', upload_to=psp_foto_passe_upload_to)
    documento_id_file = models.FileField('Documento de Identificação', upload_to=psp_documento_id_upload_to)
    
    class Meta:
        verbose_name = 'PSP'
        verbose_name_plural = 'PSP'

    def save(self, *args, **kwargs):
        if not self.nuip:
            last_id = Psp.objects.aggregate(models.Max('id'))['id__max'] or 0
            self.nuip = f'CIP{self.ANO_ATUAL:04d}{last_id+1:06d}{self.funcao}'
        super(Psp, self).save(*args, **kwargs)
    
    def __str__(self):
        return self.documento_id
    
def dspo_foto_passe_upload_to(instance, filename):
    return f'dspo/{instance.nip}/foto_passe/{filename}'

class Dspo(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE)
    nip = models.CharField('NIP', max_length=100, blank=True, null=True)
    nome = models.CharField('Nome Completo', max_length=100, blank=True, null=True)
    comando = models.CharField('Comando Provincial', max_length=100, blank=True, null=True)
    morada = models.CharField('Morada', max_length=100, blank=True, null=True)
    funcao = models.CharField('Função', max_length=100, blank=True, null=True)
    foto_passe = models.FileField('Foto Passe', upload_to=dspo_foto_passe_upload_to)
    
    class Meta:
        verbose_name = 'DSPO/CMDO PROVINCIAL'
        verbose_name_plural = 'DSPO/CMDO PROVINCIAIS'
    
    def __str__(self):
        return self.nip
    
class TecnicoDISPO(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE)
    nome = models.CharField('Nome Completo', max_length=100, blank=True, null=True)
    seccao = models.CharField('Secção',choices=[('s_licenc','Secção de Licenciamento'), ('chefe_dep','Chefe do Departamento'), ('director','Director Nacional de Segurança Pública e Operações')], max_length=50, blank=True, null=True)
    nip = models.CharField('NIP', max_length=50, blank=True, null=True)

    class Meta:
        verbose_name = 'DISPO'
        verbose_name_plural = 'DISPO'
    
    def __str__(self):
        return self.nip


