"""Painel /admin do Django (alternativa ao painel do próprio Estudaí)."""
from django.contrib import admin

from game.models import (
    Afirmacao, Evento, Licao, LicaoConcluida, Materia, Oportunidade, Perfil, Perguntas, RegistroXP,
    Resposta, Unidade,
)


# ------------------------------------------------------------ Quiz
class ItemRespostaInline(admin.TabularInline):
    model = Resposta
    extra = 4


class PerguntasAdmin(admin.ModelAdmin):
    list_display = ('pergunta', 'materia')
    list_filter = ('materia',)
    search_fields = ('pergunta',)
    inlines = [ItemRespostaInline]


admin.site.register(Perguntas, PerguntasAdmin)


# ------------------------------------------------------------ Matérias
class UnidadeInline(admin.TabularInline):
    model = Unidade
    extra = 1


class LicaoInline(admin.TabularInline):
    model = Licao
    extra = 1


@admin.register(Materia)
class MateriaAdmin(admin.ModelAdmin):
    list_display = ('nome', 'slug', 'icone', 'ordem')
    prepopulated_fields = {'slug': ('nome',)}
    inlines = [UnidadeInline]


@admin.register(Unidade)
class UnidadeAdmin(admin.ModelAdmin):
    list_display = ('titulo', 'materia', 'ordem')
    list_filter = ('materia',)
    inlines = [LicaoInline]


# ------------------------------------------------------------ Demais cadastros
@admin.register(Afirmacao)
class AfirmacaoAdmin(admin.ModelAdmin):
    list_display = ('frase', 'verdadeira', 'materia')
    list_filter = ('verdadeira', 'materia')


@admin.register(Evento)
class EventoAdmin(admin.ModelAdmin):
    list_display = ('data', 'titulo', 'tipo', 'user')
    list_filter = ('tipo',)


@admin.register(Oportunidade)
class OportunidadeAdmin(admin.ModelAdmin):
    list_display = ('titulo', 'organizacao', 'categoria', 'prazo')
    list_filter = ('categoria',)


# ------------------------------------------------------------ Progresso dos alunos (só consulta)
@admin.register(Perfil)
class PerfilAdmin(admin.ModelAdmin):
    list_display = ('user', 'turma')
    list_filter = ('turma',)


@admin.register(RegistroXP)
class RegistroXPAdmin(admin.ModelAdmin):
    list_display = ('user', 'quantidade', 'motivo', 'criado_em')
    list_filter = ('user',)


@admin.register(LicaoConcluida)
class LicaoConcluidaAdmin(admin.ModelAdmin):
    list_display = ('user', 'licao', 'acertos', 'total', 'concluida_em')
