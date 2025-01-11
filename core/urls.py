from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic.base import TemplateView
from . import views


urlpatterns = [
    path('', views.IndexView, name='index'),
    path('modulo/solicitacao-de-licenca/', views.SolicitacaoLicencaView, name='sli'),
    path('modulo/solicitacoes-de-licencas-enviadas/', views.SolicitacoesLicencasEnviadasView, name='slie'),
    path('modulo/mapa-de-pessoal/', views.MapaPessoalView, name='mapa_pessoal'),
    path('modulo/mapa-de-armas/arma/<int:mapaarmas_id>/', views.ArmaView, name='arma'),
    path('modulo/mapa-de-armas/', views.MapaArmasView, name='mapa_armas'),
    path('modulo/mapa-de-postos/', views.MapaPostosView, name='mapa_postos'),
    path('modulo/emissao-de-multas/', views.EmissaoMultasView, name='emissao_multas'),
    path('modulo/emissao-de-relatorios/', views.EmissaoRelatoriosView, name='emissao_relatorios'),
    path('modulo/comunicacao/', views.DenunciasView, name='denuncias'),
    path('modulo/avaliacao-e-validacao-dos-documentos/', views.AvaliacaoValidacaoView, name='avaliacao'),
    path('modulo/validar-usuarios/', views.ValidarUsuariosView, name='validar_usuarios'),
    path('modulo/servicos/', views.ServicosView, name='servicos'),
    path('modulo/emissao-carteiras/', views.EmissaoCarteirasView, name='emissao_carteiras'),
    path('modulo/pedidos/', views.PedidosView, name='pedidos'),
    path('modulo/pedidos/pedido/<int:pedido_id>/', views.PedidoView, name='pedido'),
    path('modulo/relatorios/', views.RelatoriosView, name='relatorios'),
    path('modulo/relatorios/<int:rel_id>/', views.RelatorioView, name='relatorio'),
    path('modulo/formacao/', views.FormacaoView, name='formacao'),
    path('modulo/prova-de-actividade/', views.ProvaActividadeView, name='prova_actividade'),
    path('modulo/enviar-comunicados/', views.EnviarComunicadosView, name='enviar_comunidados'),
    path('modulo/lista-de-envolvidos-em-crimes/', views.ListaEnvolvidosCrimesView, name='envolvidos_crimes'),
    path('minha-carteira/', views.minha_carteira, name='minha_carteira'),
    path('marcar-actividade/', views.marcar_actividade, name='marcar_actividade'),
    path('mapa-de-pessoal/', views.MapaPessoalAdmView, name='mapa_pessoal_adm'),
    path('mapa-de-armas/', views.MapaArmasAdmView, name='mapa_armas_adm'),
    path('multas-provincias/', views.MultasProvinciaisView, name='multas_provinciais'),
    path('relatorios-provinciais/', views.RelatoriosProvinciaisView, name='relatorios_provinciais'),
    path('comunicacoes-enviadas/', views.DenunciasEnviadasView, name='denuncias_enviadas'),
    path('pedidos-recebidos/', views.PedidosRecebidosView, name='pedidos_recebidos'),
    path('renderizar-carteira-frente/<int:carteira_id>/', views.render_carteira_frente, name='render_carteira_frente'),
    path('renderizar-carteira-verso/<int:carteira_id>/', views.render_carteira_verso, name='render_carteira_verso'),
    path('verificacao-de-carteira/<str:token_id>/', views.verificacao_de_carteira),
    path('api/rm_sli/<int:sli_id>/', views.remover_sli, name='remover_sli'),
    path('api/rm_pessoal/<int:Id>/', views.remover_pessoal, name='remover_pessoal'),
    path('api/atualizar-is-verified/<int:sli_id>', views.atualizar_is_verified, name='atualizar_is_verified'),
    path('consultar-empresas/', views.ConsultarEmpresas, name='consultar_empresas'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)