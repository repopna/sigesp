from django.contrib import admin
from contas.models import Centro, CustomUser, Dspo, Eps, Licenca, Sap, Psp, TecnicoDISPO
from django.contrib.auth.admin import UserAdmin

# Register your models here.

# InlineModelAdmin para perfis

class EpsInline(admin.StackedInline):
    model = Eps
    can_delete = False
    verbose_name_plural = 'Empresas Privadas de Segurança'

class CentroInLine(admin.StackedInline):
    model = Centro
    can_delete = False
    verbose_name_plural = 'Sistemas de Auto Proteção'

class SapInLine(admin.StackedInline):
    model = Sap
    can_delete = False
    verbose_name_plural = 'Sistemas de Auto Proteção'
    
class PspInLine(admin.StackedInline):
    model = Psp
    can_delete = False
    verbose_name_plural = 'Profissionais de Segurança Privada'

class DspoInLine(admin.StackedInline):
    model = Dspo
    can_delete = False
    verbose_name_plural = 'Técnicos Provinciais'

class CustomUserAdmin(UserAdmin):
    
    # Garantir que o usuário Staff não veja os outros usuários do sistema
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)

        if not request.user.is_superuser:
            qs = qs.exclude(is_superuser=True, is_staff=True)
        return qs
    
    # garantir que os usuarios staff não consigam alterar campos cruciais

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        is_superuser = request.user.is_superuser

        if not is_superuser and obj is not None:
            form.base_fields['username'].disabled = True
            form.base_fields['is_superuser'].disabled = True
            form.base_fields['user_permissions'].disabled = True
            form.base_fields['groups'].disabled = True
            form.base_fields['is_active'].disabled = True
            form.base_fields['is_staff'].disabled = True
            form.base_fields['creation_date'].disabled = True

        return form
    
    inlines = (EpsInline, CentroInLine, SapInLine, PspInLine, DspoInLine)
    list_display = ('username', 'email', 'is_verified', 'profile_type', 'creation_date')
    search_fields = ['username', 'nome', 'email', 'is_verified', 'profile_type']
    fieldsets = (
        (None, {'fields': ('username', 'email', 'password', 'profile_type')}),
        ('Permissões', {'fields': ('is_verified','is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
    )
    
    def save_model(self, request, obj, form, change):
        
        super().save_model(request, obj, form, change)
        
        # Garante que um usuário tenha apenas um perfil
        if not obj.pk and not change:
            # Verifica se o usuário já possui um perfil associado
            if Eps.objects.filter(user=obj).exists() or Sap.objects.filter(user=obj).exists() or Psp.objects.filter(user=obj).exists():
                raise ValueError("Este usuário já possui um perfil associado.")
            # Cria o perfil correspondente ao tipo
            if form.cleaned_data.get('profile_type') == 'eps':
                Eps.objects.create(user=obj)
            elif form.cleaned_data.get('profile_type') == 'centro':
                Centro.objects.create(user=obj)
            elif form.cleaned_data.get('profile_type') == 'sap':
                Sap.objects.create(user=obj)
            elif form.cleaned_data.get('profile_type') == 'psp':
                Psp.objects.create(user=obj)
            elif form.cleaned_data.get('profile_type') == 'dspo':
                Psp.objects.create(user=obj)

    def get_inline_instances(self, request, obj=None):
        # Exibe o inline de acordo com o tipo de perfil do usuário
        if obj and hasattr(obj, 'eps'):
            return [EpsInline(self.model, self.admin_site)]
        elif obj and hasattr(obj, 'centro'):
            return [CentroInLine(self.model, self.admin_site)]
        elif obj and hasattr(obj, 'sap'):
            return [SapInLine(self.model, self.admin_site)]
        elif obj and hasattr(obj, 'psp'):
            return [PspInLine(self.model, self.admin_site)]
        elif obj and hasattr(obj, 'dspo'):
            return [DspoInLine(self.model, self.admin_site)]
        return super().get_inline_instances(request, obj)

admin.site.register(CustomUser, CustomUserAdmin)
admin.site.register(Eps)
admin.site.register(Centro)
admin.site.register(Sap)
admin.site.register(Psp)
admin.site.register(Dspo)
admin.site.register(TecnicoDISPO)
admin.site.register(Licenca)

