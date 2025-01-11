from django.db import models
from django.utils import timezone
from contas.models import CustomUser

# Create your models here.

class Logs(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    acao = models.CharField(max_length=255)
    data = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f'{self.user} - {self.acao} - {self.data.strftime("%Y-%m-%d %H:%M:%S")}'