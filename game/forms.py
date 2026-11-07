"""Formulários do painel do administrador (CRUDs)."""
from django import forms

from game.models import Afirmacao, Evento, Licao, Materia, Oportunidade, Perguntas, Resposta, Unidade

# Classes visuais do Estudaí aplicadas automaticamente em cada campo
CLASSE_CAMPO = (
    'min-h-11 w-full rounded-2xl border-2 border-border bg-background px-4 py-2.5 '
    'text-sm font-semibold outline-none focus:border-primary'
)


class EstiloEstudaiMixin:
    """Coloca o visual do Estudaí em todos os campos do formulário."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for campo in self.fields.values():
            if isinstance(campo.widget, forms.CheckboxInput):
                campo.widget.attrs['class'] = 'size-5 accent-primary'
            else:
                campo.widget.attrs['class'] = CLASSE_CAMPO


# ---------------------------------------------------------------------
# MATÉRIAS
# ---------------------------------------------------------------------

class MateriaForm(EstiloEstudaiMixin, forms.ModelForm):
    class Meta:
        model = Materia
        fields = ['nome', 'slug', 'icone', 'ordem']


class UnidadeForm(EstiloEstudaiMixin, forms.ModelForm):
    """Unidade + as lições dela, digitadas uma por linha (mais rápido que um formulário por lição)."""

    licoes_texto = forms.CharField(
        label='Lições (uma por linha, na ordem da trilha)',
        widget=forms.Textarea(attrs={'rows': 5}),
    )

    class Meta:
        model = Unidade
        fields = ['titulo', 'ordem']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.pk:
            nomes = self.instance.licoes.values_list('nome', flat=True)
            self.fields['licoes_texto'].initial = '\n'.join(nomes)

    def save(self, commit=True):
        unidade = super().save(commit=True)
        nomes = [linha.strip() for linha in self.cleaned_data['licoes_texto'].splitlines() if linha.strip()]
        existentes = list(unidade.licoes.order_by('ordem', 'id'))

        # Reaproveita as lições que já existem (para não perder o progresso dos alunos)...
        for posicao, nome in enumerate(nomes):
            if posicao < len(existentes):
                licao = existentes[posicao]
                licao.nome, licao.ordem = nome, posicao
                licao.save()
            else:
                Licao.objects.create(unidade=unidade, nome=nome, ordem=posicao)
        # ...e apaga as que sobraram
        for licao in existentes[len(nomes):]:
            licao.delete()
        return unidade


# ---------------------------------------------------------------------
# QUIZ: pergunta + 4 alternativas
# ---------------------------------------------------------------------

class PerguntaForm(EstiloEstudaiMixin, forms.ModelForm):
    alternativa_1 = forms.CharField(max_length=100)
    alternativa_2 = forms.CharField(max_length=100)
    alternativa_3 = forms.CharField(max_length=100, required=False)
    alternativa_4 = forms.CharField(max_length=100, required=False)
    correta = forms.TypedChoiceField(
        label='Qual alternativa é a certa?',
        choices=[(1, 'Alternativa 1'), (2, 'Alternativa 2'), (3, 'Alternativa 3'), (4, 'Alternativa 4')],
        coerce=int,
    )

    class Meta:
        model = Perguntas
        fields = ['materia', 'pergunta']
        labels = {'materia': 'Matéria (vazio = só no Quiz relâmpago)'}

    field_order = ['materia', 'pergunta', 'alternativa_1', 'alternativa_2', 'alternativa_3',
                   'alternativa_4', 'correta', 'explicacao']

    explicacao = forms.CharField(label='Explicação', max_length=300, required=False,
                                 widget=forms.Textarea(attrs={'rows': 2}))

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Ao editar, preenche as alternativas que já existem
        if self.instance.pk:
            self.fields['explicacao'].initial = self.instance.explicacao
            for numero, resposta in enumerate(self.instance.resposta_set.order_by('id')[:4], start=1):
                self.fields[f'alternativa_{numero}'].initial = resposta.resposta_correta
                if resposta.tipo == 'certa':
                    self.fields['correta'].initial = numero

    def clean(self):
        dados = super().clean()
        correta = dados.get('correta')
        if correta and not dados.get(f'alternativa_{correta}'):
            self.add_error('correta', 'A alternativa marcada como certa está vazia.')
        return dados

    def save(self, commit=True):
        pergunta = super().save(commit=False)
        pergunta.explicacao = self.cleaned_data['explicacao']
        pergunta.save()

        # Recria as alternativas a partir do formulário
        pergunta.resposta_set.all().delete()
        for numero in range(1, 5):
            texto = self.cleaned_data.get(f'alternativa_{numero}')
            if texto:
                Resposta.objects.create(
                    pergunta=pergunta,
                    resposta_correta=texto,
                    tipo='certa' if numero == self.cleaned_data['correta'] else 'errada',
                )
        return pergunta


# ---------------------------------------------------------------------
# VERDADEIRO OU FALSO, AGENDA E OPORTUNIDADES
# ---------------------------------------------------------------------

class AfirmacaoForm(EstiloEstudaiMixin, forms.ModelForm):
    class Meta:
        model = Afirmacao
        fields = ['frase', 'verdadeira', 'materia']


class EventoForm(EstiloEstudaiMixin, forms.ModelForm):
    class Meta:
        model = Evento
        fields = ['titulo', 'tipo', 'data', 'descricao']
        widgets = {'data': forms.DateInput(attrs={'type': 'date'}, format='%Y-%m-%d')}


class OportunidadeForm(EstiloEstudaiMixin, forms.ModelForm):
    class Meta:
        model = Oportunidade
        fields = ['categoria', 'titulo', 'organizacao', 'descricao', 'prazo', 'local', 'tags']
        widgets = {'descricao': forms.Textarea(attrs={'rows': 3})}
