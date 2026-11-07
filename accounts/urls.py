from django.urls import path
from accounts.views import CriarConta, UpdateConta, DeleteConta, ListConta

app_name = 'accounts'

urlpatterns = [
    path('criar/', CriarConta.as_view(), name='criar_conta'),
    path('atualizar/<int:pk>/', UpdateConta.as_view(), name='atualizar_conta'),
    path('deletar/<int:pk>/', DeleteConta.as_view(), name='deletar_conta'),
    path('listar/', ListConta.as_view(), name='listar_contas'),
]