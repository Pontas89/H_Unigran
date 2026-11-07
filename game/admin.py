from django.contrib import admin
from game.models import Perguntas
# Register your models here.

class PerguntasAdmin(admin.ModelAdmin):
    list_display = ('pergunta', 'resposta_correta')  # Campos a serem exibidos na lista de perguntas
    search_fields = ('pergunta',)  # Campos a serem pesquisados na barra de pesquisa
    
admin.site.register(Perguntas, PerguntasAdmin)
