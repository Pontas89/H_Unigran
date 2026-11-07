from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

from game.models import TURMAS, Perfil


class CustomUserCreationForm(UserCreationForm):
    """Cadastro de aluno: dados do usuário + turma (usada no ranking de turmas).

    Usado na tela "Criar Conta" e no /admin (Accounts → Alunos).
    """

    turma = forms.ChoiceField(choices=TURMAS, initial='2º ano B', label='Turma')

    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email', 'turma', 'password1', 'password2']
        labels = {
            'username': 'Nome de usuário',
            'first_name': 'Nome',
            'last_name': 'Sobrenome',
            'email': 'E-mail',
        }

    def save(self, commit=True):
        user = super().save(commit=commit)
        if commit:
            # Cria o perfil do aluno já com a turma escolhida
            Perfil.objects.update_or_create(user=user, defaults={'turma': self.cleaned_data['turma']})
        return user
