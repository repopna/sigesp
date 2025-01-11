from django import forms
from django.core.exceptions import ValidationError
import uuid
from django.contrib.auth.forms import AuthenticationForm

class TokenForm(forms.Form):
    token = forms.CharField(max_length=36, label="Token")

    def clean_token(self):
        token_str = self.cleaned_data['token']
        try:
            # Valida se o token é um UUID válido
            token = uuid.UUID(token_str)
        except ValueError:
            raise ValidationError("O token fornecido não é válido.")
        return token
    
class CustomAuthenticationForm(AuthenticationForm):
    def clean_username(self):
        username = self.cleaned_data.get('username', '').upper()
        print(username)

        return username

