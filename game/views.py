"""Views do Estudaí.

Cada view só faz duas coisas: pega os dados (usando as classes de game/servicos.py)
e entrega para o template. Nenhum cálculo complicado fica aqui.

Organização do arquivo:
    1. Menu e mixins ........ login obrigatório, acesso de admin e dados do topo
    2. Telas do aluno ....... início, matérias, lição, jogos, ranking, calendário...
    3. API do app.js ........ XP, lição concluída, recompensa diária e Fagulha
    4. CRUDs do admin ....... matérias, quiz, verdadeiro ou falso, agenda e oportunidades

Regra de acesso: só o ADMIN (usuário com is_staff) cadastra, edita e exclui.
Os ALUNOS só jogam e registram progresso (XP e lições concluídas).
"""
import json
import logging
import random

from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.db.models import Sum
from django.db.models.functions import Coalesce
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.utils import timezone
from django.views import View
from django.views.generic import CreateView, DeleteView, ListView, TemplateView, UpdateView

from game import fagulha
from game.fagulha_contexto import montar_instrucoes
from game.forms import AfirmacaoForm, EventoForm, MateriaForm, OportunidadeForm, PerguntaForm, UnidadeForm
from game.models import (
    Afirmacao, Evento, Licao, LicaoConcluida, Materia, Oportunidade, Perguntas, RegistroXP, Unidade, perfil_de,
)
from game.servicos import Calendario, ProgressoDoAluno, Ranking, RecompensaDiaria

logger = logging.getLogger(__name__)


# =====================================================================
# 1. MENU E MIXINS
# =====================================================================

class Menu:
    """Itens do menu lateral. Os 4 primeiros também aparecem no menu de baixo do celular."""

    ITENS = [
        {'secao': 'inicio', 'url': 'game:inicio', 'icone': 'house', 'rotulo': 'Início'},
        {'secao': 'materias', 'url': 'game:materia-list', 'icone': 'graduation-cap', 'rotulo': 'Matérias'},
        {'secao': 'jogos', 'url': 'game:jogo-list', 'icone': 'gamepad-2', 'rotulo': 'Jogos'},
        {'secao': 'ranking', 'url': 'game:ranking', 'icone': 'trophy', 'rotulo': 'Ranking'},
        {'secao': 'calendario', 'url': 'game:calendario', 'icone': 'calendar-days', 'rotulo': 'Calendário'},
        {'secao': 'oportunidades', 'url': 'game:oportunidades', 'icone': 'briefcase', 'rotulo': 'Oportunidades'},
        {'secao': 'bem-estar', 'url': 'game:bem-estar', 'icone': 'heart-handshake', 'rotulo': 'Bem-estar'},
        {'secao': 'perfil', 'url': 'game:perfil', 'icone': 'user', 'rotulo': 'Perfil'},
    ]


class AlunoMixin(LoginRequiredMixin):
    """Base de toda tela do sistema.

    - Exige login (quem não está logado vai para a tela de entrar).
    - Manda para o template o que aparece em TODAS as páginas:
      menu, números do topo (XP e ofensiva) e o lembrete da Fagulha.
    """
    secao = None  # qual item do menu fica aceso

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        perfil = perfil_de(self.request.user)
        context.update({
            'menu': Menu.ITENS,
            'secao': self.secao,
            'perfil': perfil,
            'xp_total': perfil.xp_total(),
            'ofensiva': perfil.ofensiva(),
            'lembrete': Calendario(self.request.user).lembrete(),
        })
        return context


class AdminMixin(AlunoMixin, UserPassesTestMixin):
    """Telas de cadastro: só o administrador (is_staff) entra. Aluno recebe "403 Proibido"."""

    def test_func(self):
        return self.request.user.is_staff


class PaginaView(AlunoMixin, TemplateView):
    """Página simples do sistema (só precisa dizer o template e a seção do menu)."""


# =====================================================================
# 2. TELAS DO ALUNO
# =====================================================================

class InicioView(PaginaView):
    template_name = 'game/inicio.html'
    secao = 'inicio'

    META_DIARIA = 50  # XP por dia

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        progresso = ProgressoDoAluno(user)
        calendario = Calendario(user)
        recompensa = RecompensaDiaria(user)
        ranking = Ranking().alunos(Ranking.SEMANA)

        # Meta diária
        xp_hoje = (
            RegistroXP.objects
            .filter(user=user, criado_em__date=timezone.localdate())
            .aggregate(total=Coalesce(Sum('quantidade'), 0))['total']
        )
        dia_com_aula = calendario.proximo_dia_com_aula()

        context.update({
            'meta': {
                'feito': min(xp_hoje, self.META_DIARIA),
                'falta': max(0, self.META_DIARIA - xp_hoje),
                'porcentagem': min(100, round(xp_hoje / self.META_DIARIA * 100)),
            },
            'continuar': progresso.proxima_licao(),
            'progresso': progresso.por_materia(),
            'provas': calendario.proximos(5),
            'hoje': calendario.hoje,
            # Aulas: de hoje ou do próximo dia que tiver aula
            'dia_com_aula': dia_com_aula,
            'dia_com_aula_nome': Calendario.DIAS_DA_SEMANA[dia_com_aula.weekday()] if dia_com_aula else '',
            'aulas': Calendario.aulas(dia_com_aula) if dia_com_aula else [],
            # Recompensa diária
            'recompensa': {
                'dias': recompensa.dias(),
                'dia_atual': recompensa.dia_atual(),
                'xp': recompensa.xp_de_hoje(),
                'ja_resgatou': recompensa.ja_resgatou_hoje(),
            },
            # Mini ranking (top 5 da semana)
            'ranking': ranking[:5],
            'minha_posicao': Ranking.posicao_de(user, ranking),
        })
        return context


class MateriaListView(PaginaView):
    template_name = 'game/materia_list.html'
    secao = 'materias'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['progresso'] = ProgressoDoAluno(self.request.user).por_materia()
        return context


class MateriaDetailView(PaginaView):
    template_name = 'game/materia_detail.html'
    secao = 'materias'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        materia = get_object_or_404(Materia, slug=self.kwargs['slug'])
        context['materia'] = materia
        context['unidades'] = ProgressoDoAluno(self.request.user).trilha(materia)
        return context


class LicaoView(PaginaView):
    """Quiz de uma lição: usa as perguntas cadastradas na matéria da lição."""
    template_name = 'game/licao.html'
    MAXIMO_DE_PERGUNTAS = 8

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        licao = get_object_or_404(Licao.objects.select_related('unidade__materia'), pk=self.kwargs['pk'])
        materia = licao.unidade.materia

        perguntas = list(materia.perguntas.prefetch_related('resposta_set'))
        random.shuffle(perguntas)

        context.update({
            'url_sair': reverse('game:materia-detail', args=[materia.slug]),
            'url_concluir': reverse('game:licao-concluir', args=[licao.pk]),
            # Vai para o app.js como JSON (ver {{ dados_licao|json_script }} no template)
            'dados_licao': {
                'titulo': f'{materia.nome} · {licao.nome}',
                'perguntas': [p.para_o_jogo() for p in perguntas[:self.MAXIMO_DE_PERGUNTAS]],
            },
        })
        return context


class QuizRelampagoView(PaginaView):
    """Quiz relâmpago: uma pergunta aleatória de cada matéria (não conta como lição da trilha)."""
    template_name = 'game/licao.html'
    secao = 'jogos'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        perguntas = [
            random.choice(list(materia.perguntas.all()))
            for materia in Materia.objects.all()
            if materia.perguntas.exists()
        ]
        random.shuffle(perguntas)

        context['url_sair'] = reverse('game:jogo-list')
        context['dados_licao'] = {'titulo': 'Quiz relâmpago', 'perguntas': [p.para_o_jogo() for p in perguntas]}
        return context


class JogoListView(PaginaView):
    template_name = 'game/jogo_list.html'
    secao = 'jogos'


class JogoVerdadeiroFalsoView(PaginaView):
    template_name = 'game/jogo_verdadeiro_falso.html'
    secao = 'jogos'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['dados_vf'] = [
            {
                'frase': afirmacao.frase,
                'resposta': afirmacao.verdadeira,
                'materia': afirmacao.materia.nome if afirmacao.materia else 'Geral',
            }
            for afirmacao in Afirmacao.objects.select_related('materia')
        ]
        return context


class JogoMemoriaView(PaginaView):
    template_name = 'game/jogo_memoria.html'
    secao = 'jogos'


class JogoLinhaDoTempoView(PaginaView):
    template_name = 'game/jogo_linha_do_tempo.html'
    secao = 'jogos'


class RankingView(PaginaView):
    template_name = 'game/ranking.html'
    secao = 'ranking'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        ranking = Ranking()
        semana = ranking.alunos(Ranking.SEMANA)
        total = ranking.alunos(Ranking.TOTAL)

        context.update({
            'semana': semana,
            'total': total,
            'podio_semana': Ranking.podio(semana),
            'podio_total': Ranking.podio(total),
            'turmas': ranking.turmas(),
            'minha_turma': perfil_de(self.request.user).turma,
            # Os 3 últimos da liga ficam na zona de rebaixamento
            'rebaixamento': max(4, len(semana) - 2),
        })
        return context


class CalendarioView(PaginaView):
    template_name = 'game/calendario.html'
    secao = 'calendario'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        calendario = Calendario(self.request.user)
        context.update({
            'meses': calendario.meses(3),
            'detalhes': calendario.detalhes(),
            'hoje': calendario.hoje,
        })
        return context


class OportunidadesView(PaginaView):
    template_name = 'game/oportunidades.html'
    secao = 'oportunidades'

    ICONES = {'eventos': 'calendar-days', 'cursos': 'book-open', 'estagios': 'briefcase', 'concursos': 'trophy'}

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categorias'] = [
            {'valor': valor, 'nome': nome, 'icone': self.ICONES[valor]}
            for valor, nome in Oportunidade.CATEGORIAS
        ]
        context['oportunidades'] = Oportunidade.objects.all()
        return context


class BemEstarView(PaginaView):
    template_name = 'game/bem_estar.html'
    secao = 'bem-estar'


class PerfilView(PaginaView):
    template_name = 'game/perfil.html'
    secao = 'perfil'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        progresso = ProgressoDoAluno(user).por_materia()
        posicao = Ranking.posicao_de(user, Ranking().alunos(Ranking.SEMANA))
        context.update({
            'progresso': progresso,
            'minha_posicao': posicao or '–',
            'conquistas': self.conquistas(user, progresso, posicao, context['ofensiva']),
        })
        return context

    @staticmethod
    def conquistas(user, progresso, posicao, ofensiva):
        """Lista de conquistas e se o aluno já ganhou cada uma."""
        porcentagem = {item['materia'].slug: item['porcentagem'] for item in progresso}
        concluidas = list(LicaoConcluida.objects.filter(user=user))

        regras = [
            # (ícone, nome, como ganhar, ganhou?)
            ('graduation-cap', 'Primeira lição', 'Conclua sua primeira lição', bool(concluidas)),
            ('flame', 'Fogo contínuo', '7 dias de ofensiva', ofensiva >= 7),
            ('target', 'Gabaritou', '100% de acertos numa lição', any(c.total and c.acertos == c.total for c in concluidas)),
            ('trophy', 'Pódio', 'Top 3 da liga da semana', posicao is not None and posicao <= 3),
            ('sigma', 'Gênio dos números', 'Complete a trilha de Matemática', porcentagem.get('matematica') == 100),
            ('languages', 'Poliglota', 'Complete a trilha de Inglês', porcentagem.get('ingles') == 100),
        ]
        return [{'icone': i, 'nome': n, 'descricao': d, 'ganhou': g} for i, n, d, g in regras]


# =====================================================================
# 3. API USADA PELO app.js (recebe e devolve JSON)
# =====================================================================

class ApiView(LoginRequiredMixin, View):
    """Base das views chamadas pelo JavaScript."""

    @staticmethod
    def ler_json(request):
        """Lê o corpo JSON da requisição (ou {} se vier vazio/inválido)."""
        try:
            return json.loads(request.body or '{}')
        except ValueError:
            return {}

    def resposta_com_topo(self, **extras):
        """Devolve o XP total e a ofensiva atualizados (o app.js atualiza o topo da página)."""
        perfil = perfil_de(self.request.user)
        return JsonResponse({'xp_total': perfil.xp_total(), 'ofensiva': perfil.ofensiva(), **extras})


class GanharXPView(ApiView):
    """POST {quantidade, motivo}: registra XP ganho nos jogos."""
    MAXIMO_POR_VEZ = 200

    def post(self, request):
        dados = self.ler_json(request)
        try:
            quantidade = max(1, min(self.MAXIMO_POR_VEZ, int(dados.get('quantidade', 0))))
        except (TypeError, ValueError):
            return JsonResponse({'erro': 'quantidade inválida'}, status=400)

        RegistroXP.objects.create(user=request.user, quantidade=quantidade, motivo=str(dados.get('motivo', ''))[:120])
        return self.resposta_com_topo()


class ConcluirLicaoView(ApiView):
    """POST {acertos, total, xp}: marca a lição como concluída e registra o XP ganho."""

    def post(self, request, pk):
        licao = get_object_or_404(Licao, pk=pk)
        dados = self.ler_json(request)
        try:
            acertos = int(dados.get('acertos', 0))
            total = int(dados.get('total', 0))
            xp = int(dados.get('xp', 0))
        except (TypeError, ValueError):
            return JsonResponse({'erro': 'dados inválidos'}, status=400)

        LicaoConcluida.objects.update_or_create(
            user=request.user, licao=licao, defaults={'acertos': acertos, 'total': total},
        )
        if xp > 0:
            RegistroXP.objects.create(user=request.user, quantidade=min(xp, GanharXPView.MAXIMO_POR_VEZ),
                                      motivo=f'Lição: {licao.nome}')
        return self.resposta_com_topo()


class RecompensaDiariaView(ApiView):
    """POST: resgata a recompensa do dia (o servidor decide quanto XP vale)."""

    def post(self, request):
        xp = RecompensaDiaria(request.user).resgatar()
        if xp is None:
            return JsonResponse({'erro': 'Você já resgatou hoje. Volte amanhã!'}, status=400)
        return self.resposta_com_topo(xp=xp)


class FagulhaView(ApiView):
    """Recebe o histórico do chat e devolve a resposta do Gemini.

    Sem GEMINI_API_KEY (ou se der erro), responde 503/502 e o app.js usa as respostas prontas.
    """
    MENSAGENS_LEMBRADAS = 12

    def post(self, request):
        if not fagulha.gemini_configurado():
            return JsonResponse({'erro': 'GEMINI_API_KEY não configurada'}, status=503)
        try:
            dados = json.loads(request.body)
            historico = [
                {'autor': m['autor'], 'texto': str(m['texto'])[:2000]}
                for m in dados['historico'][-self.MENSAGENS_LEMBRADAS:]
            ]
            pagina = str(dados.get('pagina', ''))[:100]
        except (ValueError, KeyError, TypeError, AttributeError):
            return JsonResponse({'erro': 'Requisição inválida'}, status=400)

        try:
            resposta, modelo = fagulha.perguntar(historico, montar_instrucoes(request.user, pagina))
            print(f'[Fagulha] respondeu com o modelo {modelo}', flush=True)
            return JsonResponse({'resposta': resposta, 'modelo': modelo})
        except fagulha.FagulhaErro as erro:
            logger.warning('Fagulha: %s', erro)
            return JsonResponse({'erro': 'A Fagulha não conseguiu responder agora'}, status=502)


# =====================================================================
# 4. CRUDs DO ADMINISTRADOR
#    Todos usam os templates genéricos game/form.html e game/confirmar_exclusao.html
# =====================================================================

class CrudMixin(AdminMixin):
    """Peças comuns de todo cadastro: título da página e para onde voltar depois de salvar."""
    titulo = ''
    voltar = None  # nome da URL de volta (ex.: 'game:oportunidades')

    def get_success_url(self):
        return reverse(self.voltar)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titulo'] = self.titulo
        context['url_voltar'] = self.get_success_url()
        return context


class CriarView(CrudMixin, CreateView):
    template_name = 'game/form.html'


class EditarView(CrudMixin, UpdateView):
    template_name = 'game/form.html'


class ExcluirView(CrudMixin, DeleteView):
    template_name = 'game/confirmar_exclusao.html'


# ---------- Matérias e unidades ----------

class MateriaGerenciarView(AdminMixin, ListView):
    template_name = 'game/admin/materia_gerenciar.html'
    context_object_name = 'materias'
    secao = 'materias'

    def get_queryset(self):
        return Materia.objects.prefetch_related('unidades__licoes', 'perguntas')


class MateriaCreateView(CriarView):
    model, form_class = Materia, MateriaForm
    titulo, voltar, secao = 'Nova matéria', 'game:materia-gerenciar', 'materias'


class MateriaUpdateView(EditarView):
    model, form_class = Materia, MateriaForm
    titulo, voltar, secao = 'Editar matéria', 'game:materia-gerenciar', 'materias'


class MateriaDeleteView(ExcluirView):
    model = Materia
    titulo, voltar, secao = 'Excluir matéria', 'game:materia-gerenciar', 'materias'


class UnidadeCreateView(CriarView):
    model, form_class = Unidade, UnidadeForm
    titulo, voltar, secao = 'Nova unidade', 'game:materia-gerenciar', 'materias'

    def form_valid(self, form):
        # A unidade é criada dentro da matéria que veio na URL
        form.instance.materia = get_object_or_404(Materia, pk=self.kwargs['materia_pk'])
        return super().form_valid(form)


class UnidadeUpdateView(EditarView):
    model, form_class = Unidade, UnidadeForm
    titulo, voltar, secao = 'Editar unidade', 'game:materia-gerenciar', 'materias'


class UnidadeDeleteView(ExcluirView):
    model = Unidade
    titulo, voltar, secao = 'Excluir unidade', 'game:materia-gerenciar', 'materias'


# ---------- Quiz (perguntas) ----------

class PerguntaListView(AdminMixin, ListView):
    template_name = 'game/admin/pergunta_list.html'
    context_object_name = 'perguntas'
    secao = 'jogos'

    def get_queryset(self):
        return (
            Perguntas.objects
            .select_related('materia')
            .prefetch_related('resposta_set')
            .order_by('materia__ordem', 'id')
        )


class PerguntaCreateView(CriarView):
    model, form_class = Perguntas, PerguntaForm
    titulo, voltar, secao = 'Nova pergunta do quiz', 'game:pergunta-list', 'jogos'


class PerguntaUpdateView(EditarView):
    model, form_class = Perguntas, PerguntaForm
    titulo, voltar, secao = 'Editar pergunta do quiz', 'game:pergunta-list', 'jogos'


class PerguntaDeleteView(ExcluirView):
    model = Perguntas
    titulo, voltar, secao = 'Excluir pergunta', 'game:pergunta-list', 'jogos'


# ---------- Verdadeiro ou falso (afirmações) ----------

class AfirmacaoListView(AdminMixin, ListView):
    template_name = 'game/admin/afirmacao_list.html'
    context_object_name = 'afirmacoes'
    secao = 'jogos'

    def get_queryset(self):
        return Afirmacao.objects.select_related('materia').order_by('materia__ordem', 'id')


class AfirmacaoCreateView(CriarView):
    model, form_class = Afirmacao, AfirmacaoForm
    titulo, voltar, secao = 'Nova afirmação', 'game:afirmacao-list', 'jogos'


class AfirmacaoUpdateView(EditarView):
    model, form_class = Afirmacao, AfirmacaoForm
    titulo, voltar, secao = 'Editar afirmação', 'game:afirmacao-list', 'jogos'


class AfirmacaoDeleteView(ExcluirView):
    model = Afirmacao
    titulo, voltar, secao = 'Excluir afirmação', 'game:afirmacao-list', 'jogos'


# ---------- Agenda (eventos do calendário) ----------

class EventoCreateView(CriarView):
    model, form_class = Evento, EventoForm
    titulo, voltar, secao = 'Adicionar à agenda', 'game:calendario', 'calendario'

    def get_initial(self):
        # Vindo do calendário com ?data=2026-11-20, a data já aparece preenchida
        return {'data': self.request.GET.get('data') or timezone.localdate()}


class EventoUpdateView(EditarView):
    model, form_class = Evento, EventoForm
    titulo, voltar, secao = 'Editar compromisso', 'game:calendario', 'calendario'


class EventoDeleteView(ExcluirView):
    model = Evento
    titulo, voltar, secao = 'Excluir compromisso', 'game:calendario', 'calendario'


# ---------- Oportunidades ----------

class OportunidadeCreateView(CriarView):
    model, form_class = Oportunidade, OportunidadeForm
    titulo, voltar, secao = 'Nova oportunidade', 'game:oportunidades', 'oportunidades'


class OportunidadeUpdateView(EditarView):
    model, form_class = Oportunidade, OportunidadeForm
    titulo, voltar, secao = 'Editar oportunidade', 'game:oportunidades', 'oportunidades'


class OportunidadeDeleteView(ExcluirView):
    model = Oportunidade
    titulo, voltar, secao = 'Excluir oportunidade', 'game:oportunidades', 'oportunidades'
