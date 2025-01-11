from django.shortcuts import redirect, render
from django.urls import reverse
from notifications.models import Notification


# Create your views here.

def NotificacoesView(request):

    notificacoes = Notification.objects.filter(recipient=request.user).order_by('-timestamp')
    notificacoes_n_lidas = notificacoes.filter(unread=True).count()

    return render(request, 'views/notificacoes_view.html', { 'notificacoes': notificacoes, 'notificacoes_n_lidas': notificacoes_n_lidas})

def LerTudoView(request):
    notifications = Notification.objects.filter(recipient=request.user, unread=True)
    for notification in notifications:
        notification.mark_as_read()
    return redirect('notificacoes')


def mark_as_read(request, notification_id):
    notification = Notification.objects.get(id=notification_id)
    notification.mark_as_read()
    return redirect('notificacoes')