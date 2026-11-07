"""Cadastro de alunos pelo /admin (com Jazzmin).

Usa o UserAdmin do Django, que salva a senha com segurança (hash),
e o mesmo formulário da tela "Cadastre-se" (com a turma do aluno).
"""
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from accounts.forms import CustomUserCreationForm
from accounts.models import Aluno
from game.models import Perfil


@admin.register(Aluno)
class AlunoAdmin(UserAdmin):
    # Formulário de "Adicionar aluno": dados + turma + senha (2x)
    add_form = CustomUserCreationForm
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'first_name', 'last_name', 'email', 'turma', 'password1', 'password2'),
        }),
    )

    list_display = ('username', 'first_name', 'last_name', 'email', 'turma', 'is_active')
    list_filter = ('is_active', 'perfil__turma')
    search_fields = ('username', 'first_name', 'last_name', 'email')

    def get_queryset(self, request):
        # Só alunos: administradores ficam em "Usuários"
        return super().get_queryset(request).filter(is_staff=False).select_related('perfil')

    @admin.display(description='Turma')
    def turma(self, obj):
        perfil = getattr(obj, 'perfil', None)
        return perfil.turma if perfil else '—'

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        # Ao criar, guarda a turma escolhida no perfil do aluno
        if not change and 'turma' in form.cleaned_data:
            Perfil.objects.update_or_create(user=obj, defaults={'turma': form.cleaned_data['turma']})
