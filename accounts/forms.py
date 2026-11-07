from django import forms
from accounts.models import Account

class AlunoForm(forms.ModelForm):
    class Meta:
        model = Account
        fields = ['username', 'email', 'password', 'codigo_aluno']
        widgets = {
            'password': forms.PasswordInput(),
        }