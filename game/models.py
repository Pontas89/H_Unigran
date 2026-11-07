"""Models do Estudaí.

Organização:
    1. Matérias e trilhas ......... Materia > Unidade > Licao
    2. Jogos ...................... Perguntas + Resposta (quiz) e Afirmacao (verdadeiro ou falso)
    3. Aluno ...................... Perfil, RegistroXP (pontos) e LicaoConcluida (progresso)
    4. Calendário ................. Evento
    5. Oportunidades .............. Oportunidade
"""
import datetime

from django.conf import settings
from django.db import models
from django.db.models import Sum
from django.utils import timezone


# =====================================================================
# 1. MATÉRIAS E TRILHAS
# =====================================================================

class Materia(models.Model):
    nome = models.CharField(max_length=50)
    professor = models.CharField(max_length=60, blank=True)
    slug = models.SlugField(unique=True, help_text='Usado na URL. Ex.: matematica')
    icone = models.CharField(
        max_length=40,
        default='book-open',
        help_text='Nome do ícone Lucide (lucide.dev/icons). Ex.: sigma, atom, leaf',
    )
    ordem = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['ordem', 'nome']
        verbose_name = 'Matéria'

    def __str__(self):
        return self.nome

    def licoes_em_ordem(self):
        """Todas as lições da matéria, na ordem da trilha (unidade 1, unidade 2...)."""
        return Licao.objects.filter(unidade__materia=self).order_by('unidade__ordem', 'unidade__id', 'ordem', 'id')


class Unidade(models.Model):
    materia = models.ForeignKey(Materia, on_delete=models.CASCADE, related_name='unidades')
    titulo = models.CharField(max_length=80)
    ordem = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['ordem', 'id']

    def __str__(self):
        return f'{self.materia} · {self.titulo}'


class Licao(models.Model):
    unidade = models.ForeignKey(Unidade, on_delete=models.CASCADE, related_name='licoes')
    nome = models.CharField(max_length=80)
    ordem = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['ordem', 'id']
        verbose_name = 'Lição'
        verbose_name_plural = 'Lições'

    def __str__(self):
        return self.nome


# =====================================================================
# 2. JOGOS
# =====================================================================

class Perguntas(models.Model):
    """Pergunta do quiz (lições e Quiz relâmpago). As alternativas ficam em Resposta."""
    pergunta = models.CharField(max_length=200)
    materia = models.ForeignKey(Materia, on_delete=models.CASCADE, null=True, blank=True, related_name='perguntas')
    explicacao = models.CharField(max_length=300, blank=True, help_text='Aparece depois que o aluno responde.')

    class Meta:
        verbose_name = 'Pergunta'

    def __str__(self):
        return self.pergunta

    def para_o_jogo(self):
        """Formato usado pelo app.js: {pergunta, alternativas, correta, explicacao}."""
        alternativas = list(self.resposta_set.order_by('id'))
        correta = next((i for i, r in enumerate(alternativas) if r.tipo == 'certa'), 0)
        return {
            'pergunta': self.pergunta,
            'alternativas': [r.resposta_correta for r in alternativas],
            'correta': correta,
            'explicacao': self.explicacao,
        }


class Resposta(models.Model):
    """Alternativa de uma pergunta. Só uma deve ser do tipo 'certa'."""

    CHOICES_TIPO = [
        ('certa', 'Certa'),
        ('errada', 'Errada'),
    ]
    pergunta = models.ForeignKey(Perguntas, on_delete=models.CASCADE)
    resposta_correta = models.CharField('texto da alternativa', max_length=100)
    tipo = models.CharField(max_length=10, choices=CHOICES_TIPO)

    def __str__(self):
        return self.resposta_correta


class Afirmacao(models.Model):
    """Frase do jogo Verdadeiro ou falso."""
    frase = models.CharField(max_length=200)
    verdadeira = models.BooleanField(default=True, help_text='Marque se a frase é verdadeira.')
    materia = models.ForeignKey(Materia, on_delete=models.SET_NULL, null=True, blank=True)

    class Meta:
        verbose_name = 'Afirmação'
        verbose_name_plural = 'Afirmações'

    def __str__(self):
        return self.frase


# =====================================================================
# 3. ALUNO: perfil, XP e progresso
# =====================================================================

TURMAS = [
    ('1º ano A', '1º ano A'), ('1º ano B', '1º ano B'),
    ('2º ano A', '2º ano A'), ('2º ano B', '2º ano B'), ('2º ano C', '2º ano C'),
    ('3º ano A', '3º ano A'), ('3º ano B', '3º ano B'),
]


class Perfil(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='perfil')
    turma = models.CharField(max_length=20, choices=TURMAS, default='2º ano B')

    class Meta:
        verbose_name_plural = 'Perfis'

    def __str__(self):
        return f'{self.user} ({self.turma})'

    # ---------- números do aluno (calculados a partir dos registros de XP) ----------

    def xp_total(self):
        return RegistroXP.objects.filter(user=self.user).aggregate(total=Sum('quantidade'))['total'] or 0

    def xp_semana(self):
        return RegistroXP.objects.filter(user=self.user, criado_em__gte=inicio_da_semana()).aggregate(
            total=Sum('quantidade'))['total'] or 0

    def ofensiva(self):
        """Dias seguidos ganhando XP (vale até ontem: hoje ainda dá tempo de manter o fogo)."""
        dias = set(
            timezone.localtime(data).date()
            for data in RegistroXP.objects.filter(user=self.user).values_list('criado_em', flat=True)
        )
        dia = timezone.localdate()
        if dia not in dias:
            dia -= datetime.timedelta(days=1)
        seguidos = 0
        while dia in dias:
            seguidos += 1
            dia -= datetime.timedelta(days=1)
        return seguidos

    def nivel(self):
        """A cada 1.000 XP sobe um nível."""
        return self.xp_total() // 1000 + 1

    def xp_para_proximo_nivel(self):
        return 1000 - self.xp_total() % 1000

    def progresso_nivel(self):
        """Quanto (em %) já andou dentro do nível atual."""
        return self.xp_total() % 1000 // 10

    def iniciais(self):
        nome = self.user.get_full_name() or self.user.username
        return ''.join(parte[0] for parte in nome.split()[:2]).upper()


def inicio_da_semana():
    """Segunda-feira 00:00 da semana atual (a liga reinicia toda segunda)."""
    hoje = timezone.localdate()
    segunda = hoje - datetime.timedelta(days=hoje.weekday())
    return timezone.make_aware(datetime.datetime.combine(segunda, datetime.time.min))


def perfil_de(user):
    """Pega (ou cria na hora) o perfil do usuário."""
    perfil, _ = Perfil.objects.get_or_create(user=user)
    return perfil


class RegistroXP(models.Model):
    """Cada vez que o aluno ganha XP (lição, jogo, recompensa) vira uma linha aqui."""
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='registros_xp')
    quantidade = models.PositiveIntegerField()
    motivo = models.CharField(max_length=120, blank=True)
    criado_em = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ['-criado_em']
        verbose_name = 'Registro de XP'
        verbose_name_plural = 'Registros de XP'

    def __str__(self):
        return f'{self.user} +{self.quantidade} XP ({self.motivo})'


class LicaoConcluida(models.Model):
    """Guarda quais lições cada aluno já terminou (é daqui que sai o progresso por matéria)."""
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='licoes_concluidas')
    licao = models.ForeignKey(Licao, on_delete=models.CASCADE)
    acertos = models.PositiveIntegerField(default=0)
    total = models.PositiveIntegerField(default=0)
    concluida_em = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['user', 'licao']
        verbose_name = 'Lição concluída'
        verbose_name_plural = 'Lições concluídas'


# =====================================================================
# 4. CALENDÁRIO
# =====================================================================

class Evento(models.Model):
    TIPOS = [
        ('prova', 'Prova'),
        ('simulado', 'Simulado'),
        ('entrega', 'Entrega'),
        ('evento', 'Evento'),
        ('feriado', 'Feriado'),
    ]
    titulo = models.CharField(max_length=100)
    descricao = models.CharField('descrição', max_length=200, blank=True)
    data = models.DateField()
    tipo = models.CharField(max_length=10, choices=TIPOS, default='evento')
    # Sem dono = evento da escola (todos veem). Com dono = compromisso pessoal do aluno.
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, blank=True)

    class Meta:
        ordering = ['data', 'id']

    def __str__(self):
        return f'{self.data:%d/%m} · {self.titulo}'

    # Cores usadas no calendário (classes do Tailwind que já existem no CSS)
    CORES_PONTO = {
        'prova': 'bg-primary', 'simulado': 'bg-accent-foreground', 'entrega': 'bg-foreground',
        'evento': 'bg-muted-foreground', 'feriado': 'bg-border-strong',
    }
    CORES_SELO = {
        'prova': 'bg-primary text-primary-foreground', 'simulado': 'bg-accent text-accent-foreground',
        'entrega': 'bg-foreground text-background', 'evento': 'bg-muted text-muted-foreground',
        'feriado': 'border-2 border-border text-muted-foreground',
    }

    def cor_ponto(self):
        return self.CORES_PONTO.get(self.tipo, 'bg-muted-foreground')

    def cor_selo(self):
        return self.CORES_SELO.get(self.tipo, 'bg-muted text-muted-foreground')


# =====================================================================
# 5. OPORTUNIDADES
# =====================================================================

class Oportunidade(models.Model):
    CATEGORIAS = [
        ('eventos', 'Eventos'),
        ('cursos', 'Cursos'),
        ('estagios', 'Estágios'),
        ('concursos', 'Concursos'),
    ]
    categoria = models.CharField(max_length=10, choices=CATEGORIAS)
    organizacao = models.CharField('organização', max_length=80)
    titulo = models.CharField('título', max_length=100)
    descricao = models.CharField('descrição', max_length=250)
    prazo = models.CharField(max_length=60, help_text='Ex.: Inscrições abertas, Em 2 semanas')
    local = models.CharField(max_length=60)
    tags = models.CharField(max_length=100, blank=True, help_text='Separadas por vírgula. Ex.: Gratuito, Online')

    class Meta:
        ordering = ['categoria', 'id']

    def __str__(self):
        return self.titulo

    def lista_de_tags(self):
        return [tag.strip() for tag in self.tags.split(',') if tag.strip()]
