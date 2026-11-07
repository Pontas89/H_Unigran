"""Telas de acesso do Estudaí: apresentação, entrar, sair e criar conta.

O visual vem da pasta escola_futuro (CSS em accounts/static/accounts/css/).
O login usa o sistema de autenticação do próprio Django (senhas com hash).
"""
from django.contrib.auth.views import LoginView, LogoutView
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.views.generic import CreateView, TemplateView

from accounts.forms import CustomUserCreationForm


class ApresentacaoView(TemplateView):
    """Página inicial do site (/). Quem já entrou vai direto para o início do sistema."""
    template_name = 'accounts/apresentacao.html'

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect('game:inicio')
        return super().dispatch(request, *args, **kwargs)


class UserLoginView(LoginView):
    """Entrar com usuário e senha. Se já estiver logado, pula esta tela."""
    template_name = 'accounts/user_login.html'
    redirect_authenticated_user = True


class UserLogoutView(LogoutView):
    """Sair (só aceita POST, por segurança). Depois volta para a tela de entrar."""


class UserRegisterView(CreateView):
    """Criar conta de aluno. Depois do cadastro, vai para a tela de entrar."""
    template_name = 'accounts/user_form_register.html'
    form_class = CustomUserCreationForm
    success_url = reverse_lazy('accounts:login')
