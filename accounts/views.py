from django.shortcuts import render
from accounts.models import Account
from django.views.generic import CreateView, UpdateView, DeleteView, ListView
from accounts.forms import AlunoForm

# Create your views here.

class CriarConta(CreateView):
    model = Account
    form_class = AlunoForm
    template_name = 'accounts/criar_conta.html'
    success_url = '/login/'  # Redireciona para a página de login após criar a conta

class UpdateConta(UpdateView):
    model = Account
    template_name = 'accounts/atualizar_conta.html'
    fields = ['username', 'email', 'password', 'codigo_aluno']
    success_url = '/perfil/'  # Redireciona para a página de perfil após atualizar a conta

class DeleteConta(DeleteView):
    model = Account
    template_name = 'accounts/deletar_conta.html'
    success_url = '/login/'  # Redireciona para a página de login após deletar a conta

class ListConta(ListView):
    model = Account
    template_name = 'accounts/listar_contas.html'
    context_object_name = 'contas'  # Nome do contexto para acessar as contas na template
