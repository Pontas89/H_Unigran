"""Regras de negócio do Estudaí, organizadas em classes.

Por que um arquivo separado?
    As views só devem "receber o pedido e montar a resposta". Os cálculos
    (progresso, ranking, calendário, recompensa...) moram aqui, em classes
    com nomes claros. Assim fica fácil de ler, testar e reaproveitar
    (a Fagulha, por exemplo, usa as mesmas classes que as telas).

Classes:
    ProgressoDoAluno ... lições concluídas, trilha de cada matéria e % por matéria
    Ranking ............ liga da semana, XP total e ranking de turmas
    Calendario ......... meses, eventos por dia, aulas e próximos compromissos
    RecompensaDiaria ... os 7 dias de recompensa (sequência de dias seguidos)
"""
import calendar
import datetime

from django.contrib.auth.models import User
from django.db.models import Q, Sum
from django.db.models.functions import Coalesce
from django.utils import timezone

from game.dados_iniciais import AULAS_POR_DIA_DA_SEMANA
from game.models import Evento, LicaoConcluida, Materia, Perfil, RegistroXP, inicio_da_semana, perfil_de


# =====================================================================
# PROGRESSO DO ALUNO
# =====================================================================

class ProgressoDoAluno:
    """Tudo sobre o avanço de UM aluno nas trilhas das matérias."""

    # Zigue-zague da trilha (classes do Tailwind que já existem no CSS)
    DESLOCAMENTOS = ['translate-x-0', 'translate-x-12', 'translate-x-20', 'translate-x-12',
                     'translate-x-0', '-translate-x-12', '-translate-x-20', '-translate-x-12']

    def __init__(self, user):
        self.user = user
        # Busca uma vez só os ids das lições que o aluno já terminou
        self.licoes_feitas = set(
            LicaoConcluida.objects.filter(user=user).values_list('licao_id', flat=True)
        )

    def trilha(self, materia):
        """Unidades da matéria com o status de cada lição.

        concluida -> já terminou | atual -> a próxima a fazer | bloqueada -> vem depois da atual
        """
        ja_achou_atual = False
        posicao = 0
        unidades = []

        for unidade in materia.unidades.prefetch_related('licoes'):
            licoes = []
            for licao in unidade.licoes.all():
                if licao.id in self.licoes_feitas:
                    status = 'concluida'
                elif not ja_achou_atual:
                    status = 'atual'
                    ja_achou_atual = True
                else:
                    status = 'bloqueada'

                licoes.append({
                    'licao': licao,
                    'status': status,
                    'deslocamento': self.DESLOCAMENTOS[posicao % len(self.DESLOCAMENTOS)],
                })
                posicao += 1

            unidades.append({'unidade': unidade, 'licoes': licoes})
        return unidades

    def por_materia(self):
        """Cada matéria com: lições concluídas, total, % e a próxima lição a fazer."""
        resultado = []
        for materia in Materia.objects.all():
            licoes = list(materia.licoes_em_ordem())
            concluidas = sum(1 for licao in licoes if licao.id in self.licoes_feitas)

            resultado.append({
                'materia': materia,
                'concluidas': concluidas,
                'total': len(licoes),
                'porcentagem': round(concluidas / len(licoes) * 100) if licoes else 0,
                'proxima': next((licao for licao in licoes if licao.id not in self.licoes_feitas), None),
            })
        return resultado

    def proxima_licao(self):
        """A próxima lição da primeira matéria que ainda não foi terminada (botão "Continuar")."""
        return next((item['proxima'] for item in self.por_materia() if item['proxima']), None)


# =====================================================================
# RANKING
# =====================================================================

class Ranking:
    """Classificação dos alunos. Administradores (is_staff) ficam de fora."""

    SEMANA = 'semana'  # XP ganho desde segunda-feira (liga da semana)
    TOTAL = 'total'    # XP de todos os tempos

    def alunos(self, ordem=SEMANA):
        """Lista de alunos já ordenada, com posição, iniciais, turma, ofensiva e XP."""
        alunos = (
            User.objects
            .filter(is_staff=False, is_active=True)
            .annotate(
                total=Coalesce(Sum('registros_xp__quantidade'), 0),
                semana=Coalesce(
                    Sum('registros_xp__quantidade', filter=Q(registros_xp__criado_em__gte=inicio_da_semana())),
                    0,
                ),
            )
            .order_by(f'-{ordem}', 'first_name', 'username')
        )

        linhas = []
        for posicao, aluno in enumerate(alunos, start=1):
            perfil = perfil_de(aluno)
            linhas.append({
                'posicao': posicao,
                'aluno': aluno,
                'nome': aluno.get_full_name() or aluno.username,
                'primeiro_nome': aluno.first_name or aluno.username,
                'iniciais': perfil.iniciais(),
                'turma': perfil.turma,
                'ofensiva': perfil.ofensiva(),
                'xp': getattr(aluno, ordem),
            })
        return linhas

    @staticmethod
    def podio(linhas):
        """Os 3 primeiros na ordem em que aparecem na tela: 2º, 1º, 3º."""
        return [linhas[i] for i in (1, 0, 2) if i < len(linhas)]

    @staticmethod
    def posicao_de(user, linhas):
        """Posição do usuário na lista (ou None se ele não estiver nela, ex.: admin)."""
        return next((linha['posicao'] for linha in linhas if linha['aluno'] == user), None)

    def turmas(self):
        """Soma do XP dos alunos de cada turma, com a largura da barra (maior turma = 100%)."""
        turmas = list(
            Perfil.objects
            .filter(user__is_staff=False)
            .values('turma')
            .annotate(xp=Coalesce(Sum('user__registros_xp__quantidade'), 0))
            .order_by('-xp')
        )
        maior = max((turma['xp'] for turma in turmas), default=0) or 1

        return [
            {
                'posicao': posicao,
                'turma': turma['turma'],
                'xp': turma['xp'],
                # str() para o CSS receber "64.7" (e não "64,7" do formato brasileiro)
                'largura': str(round(turma['xp'] / maior * 100, 1)),
            }
            for posicao, turma in enumerate(turmas, start=1)
        ]


# =====================================================================
# CALENDÁRIO
# =====================================================================

class Calendario:
    """Agenda que um usuário enxerga: eventos da escola + compromissos dele."""

    MESES = ['janeiro', 'fevereiro', 'março', 'abril', 'maio', 'junho', 'julho', 'agosto',
             'setembro', 'outubro', 'novembro', 'dezembro']
    DIAS_DA_SEMANA = ['segunda', 'terça', 'quarta', 'quinta', 'sexta', 'sábado', 'domingo']

    def __init__(self, user):
        self.user = user
        self.hoje = timezone.localdate()

    def eventos(self):
        """Eventos sem dono (da escola) + os do próprio usuário."""
        return Evento.objects.filter(Q(user__isnull=True) | Q(user=self.user))

    def proximos(self, quantidade=5):
        """Próximos compromissos a partir de hoje."""
        return self.eventos().filter(data__gte=self.hoje)[:quantidade]

    def eventos_por_dia(self):
        por_dia = {}
        for evento in self.eventos():
            por_dia.setdefault(evento.data, []).append(evento)
        return por_dia

    def meses(self, quantidade=3):
        """Grades dos próximos meses (domingo é o primeiro dia da semana)."""
        por_dia = self.eventos_por_dia()
        meses = []
        ano, mes = self.hoje.year, self.hoje.month

        for _ in range(quantidade):
            semanas = calendar.Calendar(firstweekday=6).monthdatescalendar(ano, mes)
            dias = [
                {'data': dia, 'do_mes': dia.month == mes, 'hoje': dia == self.hoje, 'eventos': por_dia.get(dia, [])}
                for semana in semanas
                for dia in semana
            ]
            meses.append({'id': f'{ano}-{mes:02d}', 'nome': f'{self.MESES[mes - 1]} de {ano}', 'dias': dias})
            ano, mes = (ano + 1, 1) if mes == 12 else (ano, mes + 1)
        return meses

    def detalhes(self):
        """Um painel para cada dia que tem evento (e para hoje)."""
        por_dia = self.eventos_por_dia()
        return [
            {'data': dia, 'hoje': dia == self.hoje, 'eventos': por_dia.get(dia, []), 'aulas': self.aulas(dia)}
            for dia in sorted(set(por_dia) | {self.hoje})
        ]

    @staticmethod
    def aulas(dia):
        """Aulas do dia da semana, com o professor e o ícone da matéria (se ela estiver cadastrada)."""
        materias = {m.nome: m for m in Materia.objects.all()}
        aulas = []
        for aula in AULAS_POR_DIA_DA_SEMANA.get(dia.weekday(), []):
            materia = materias.get(aula['materia'])
            aulas.append({
                **aula,
                'professor': materia.professor if materia else '',
                'icone': materia.icone if materia else 'book-open',
            })
        return aulas

    def proximo_dia_com_aula(self):
        """Hoje, se tiver aula; senão o próximo dia útil com aula."""
        for adiante in range(8):
            dia = self.hoje + datetime.timedelta(days=adiante)
            if AULAS_POR_DIA_DA_SEMANA.get(dia.weekday()):
                return dia
        return None

    def lembrete(self):
        """O compromisso mais próximo (hoje ou nos próximos 3 dias) para a Fagulha lembrar."""
        limite = self.hoje + datetime.timedelta(days=3)
        evento = self.eventos().filter(data__gte=self.hoje, data__lte=limite).exclude(tipo='feriado').first()
        if not evento:
            return None

        dias = (evento.data - self.hoje).days
        quando = 'é hoje' if dias == 0 else 'é amanhã' if dias == 1 else f'é em {dias} dias'
        return {
            'texto': f'{evento.titulo} {quando}.',
            'pedido': f'Me ajude a me preparar para: {evento.titulo}'
                      + (f' — {evento.descricao}' if evento.descricao else '') + '.',
        }


# =====================================================================
# RECOMPENSA DIÁRIA
# =====================================================================

class RecompensaDiaria:
    """Recompensa de 7 dias: quem resgata em dias seguidos ganha cada vez mais XP.

    Se pular um dia, volta para o Dia 1. Depois do Dia 7, recomeça.
    """

    MOTIVO = 'Recompensa diária'
    XP_POR_DIA = [10, 15, 20, 25, 30, 40, 100]  # D1 ... D7

    def __init__(self, user):
        self.user = user
        self.hoje = timezone.localdate()
        self.dias_resgatados = set(
            timezone.localtime(momento).date()
            for momento in RegistroXP.objects.filter(user=user, motivo=self.MOTIVO).values_list('criado_em', flat=True)
        )

    def ja_resgatou_hoje(self):
        return self.hoje in self.dias_resgatados

    def _sequencia_ate_ontem(self):
        """Quantos dias seguidos resgatou, terminando ontem."""
        seguidos, dia = 0, self.hoje - datetime.timedelta(days=1)
        while dia in self.dias_resgatados:
            seguidos += 1
            dia -= datetime.timedelta(days=1)
        return seguidos

    def dia_atual(self):
        """Número do dia (1 a 7) da recompensa de hoje."""
        return self._sequencia_ate_ontem() % 7 + 1

    def xp_de_hoje(self):
        return self.XP_POR_DIA[self.dia_atual() - 1]

    def dias(self):
        """Os 7 quadradinhos da tela: 'resgatado', 'hoje' ou 'bloqueado'."""
        atual = self.dia_atual()
        quadrados = []
        for numero, xp in enumerate(self.XP_POR_DIA, start=1):
            if numero < atual or (numero == atual and self.ja_resgatou_hoje()):
                estado = 'resgatado'
            elif numero == atual:
                estado = 'hoje'
            else:
                estado = 'bloqueado'
            quadrados.append({'numero': numero, 'xp': xp, 'estado': estado})
        return quadrados

    def resgatar(self):
        """Dá o XP de hoje (uma vez por dia). Retorna o XP ganho, ou None se já resgatou."""
        if self.ja_resgatou_hoje():
            return None
        xp = self.xp_de_hoje()
        RegistroXP.objects.create(user=self.user, quantidade=xp, motivo=self.MOTIVO)
        self.dias_resgatados.add(self.hoje)
        return xp
