from django.contrib import admin
from game.models import Perguntas, Resposta
# Register your models here.

class ItemRespostaInline(admin.TabularInline):
    model = Resposta
    extra = 4  
    
class PerguntasAdmin(admin.ModelAdmin):
    list_display = ('pergunta',) 
    search_fields = ('pergunta',)
    inlines = [ItemRespostaInline]  

admin.site.register(Perguntas, PerguntasAdmin)

