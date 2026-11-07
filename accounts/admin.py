from django.contrib import admin
from accounts.models import Account

# Register your models here.

class AccountAdmin(admin.ModelAdmin):
    list_display = ('username', 'email', 'codigo_aluno')  # Campos a serem exibidos na lista de contas
    search_fields = ('username', 'email', 'codigo_aluno')  # Campos a serem pesquisados na barra de pesquisa

admin.site.register(Account, AccountAdmin)