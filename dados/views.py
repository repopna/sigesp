from django.http import JsonResponse
from django.views import View
from django.db.models import Count
from datetime import datetime
from contas.models import Centro, CustomUser, Eps, Sap, Psp, Dspo
from core.models import Pedido
from django.contrib.auth.decorators import login_required

class UsuariosJSONView(View):
    def get_labels(self):
        return [
            "Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho",
            "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"
        ]
    
    def get_providers(self):
        return [
            "EPS", "SAP","CENTRO" , "PSP", "DSPO"
        ]
    
    def get_data(self):
        current_year = datetime.now().year
        profiles = ['eps', 'sap', 'centro' , 'psp', 'dspo']
        data = {profile: [0] * 12 for profile in profiles}
        
        for profile in profiles:
            profile_model = {
                'eps': Eps,
                'sap': Sap,
                'centro': Centro,
                'psp': Psp,
                'dspo': Dspo
            }[profile]

            users = profile_model.objects.filter(user__creation_date__year=current_year).values_list('user__creation_date', flat=True)
            
            for date in users:
                month = date.month
                data[profile][month - 1] += 1
        
        return data
    
    def get(self, request, *args, **kwargs):
        data = {
            'labels': self.get_labels(),
            'datasets': [{
                'label': provider,
                'data': self.get_data()[provider.lower()],
                'borderColor': 'rgba(75, 192, 192, 1)',
                'backgroundColor': 'rgba(75, 192, 192, 0.2)'
            } for provider in self.get_providers()]
        }
        return JsonResponse(data)

class PedidosJSONView(View):
    def get(self, request, *args, **kwargs):
        pedidos = Pedido.objects.values('tipo_pedido').annotate(count=Count('tipo_pedido')).order_by('tipo_pedido')
        
        labels = [pedido['tipo_pedido'] for pedido in pedidos]
        data = [pedido['count'] for pedido in pedidos]
        
        
        return JsonResponse({
            'labels': labels,
            'data': data
        })