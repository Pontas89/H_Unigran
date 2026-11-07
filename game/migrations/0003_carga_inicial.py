"""Carga inicial do Estudaí: preenche o banco com os dados que antes eram fixos no HTML/JS.

Roda sozinha no `python manage.py migrate`. Os dados ficam em game/dados_iniciais.py.
"""
import datetime

from django.db import migrations
from django.utils import timezone

from game import dados_iniciais as D


def carregar(apps, schema_editor):
    Materia = apps.get_model('game', 'Materia')
    Unidade = apps.get_model('game', 'Unidade')
    Licao = apps.get_model('game', 'Licao')
    Perguntas = apps.get_model('game', 'Perguntas')
    Resposta = apps.get_model('game', 'Resposta')
    Afirmacao = apps.get_model('game', 'Afirmacao')
    Evento = apps.get_model('game', 'Evento')
    Oportunidade = apps.get_model('game', 'Oportunidade')
    Perfil = apps.get_model('game', 'Perfil')
    RegistroXP = apps.get_model('game', 'RegistroXP')
    User = apps.get_model('auth', 'User')

    # ---------- 1. Matérias, unidades e lições ----------
    materias = {}
    for ordem_materia, m in enumerate(D.MATERIAS):
        materia = Materia.objects.create(
            nome=m['nome'], professor=m['professor'], slug=m['slug'], icone=m['icone'], ordem=ordem_materia,
        )
        materias[m['slug']] = materia
        for ordem_unidade, u in enumerate(m['unidades']):
            unidade = Unidade.objects.create(materia=materia, titulo=u['titulo'], ordem=ordem_unidade)
            for ordem_licao, nome in enumerate(u['licoes']):
                Licao.objects.create(unidade=unidade, nome=nome, ordem=ordem_licao)

    # ---------- 2. Quiz: perguntas e alternativas ----------
    for p in D.PERGUNTAS:
        pergunta = Perguntas.objects.create(
            pergunta=p['pergunta'],
            materia=materias.get(p['materia']),
            explicacao=p['explicacao'],
        )
        for indice, texto in enumerate(p['alternativas']):
            Resposta.objects.create(
                pergunta=pergunta,
                resposta_correta=texto,
                tipo='certa' if indice == p['correta'] else 'errada',
            )

    # ---------- 3. Verdadeiro ou falso ----------
    for a in D.AFIRMACOES:
        Afirmacao.objects.create(frase=a['frase'], verdadeira=a['verdadeira'], materia=materias.get(a['materia']))

    # ---------- 4. Agenda da escola e oportunidades ----------
    for e in D.EVENTOS:
        Evento.objects.create(data=e['data'], tipo=e['tipo'], titulo=e['titulo'], descricao=e['descricao'])

    for o in D.OPORTUNIDADES:
        Oportunidade.objects.create(**o)

    # ---------- 5. Colegas de demonstração do ranking ----------
    # Cria um registro de XP por dia de ofensiva, respeitando o XP da semana e o total.
    agora = timezone.now()
    hoje = timezone.localdate()
    segunda = hoje - datetime.timedelta(days=hoje.weekday())

    for aluno in D.ALUNOS_DEMO:
        if User.objects.filter(username=aluno['username']).exists():
            continue
        user = User.objects.create(
            username=aluno['username'],
            first_name=aluno['first_name'],
            last_name=aluno['last_name'],
            password='!',  # senha bloqueada: é só um colega de demonstração
        )
        Perfil.objects.create(user=user, turma=aluno['turma'])

        dias = [hoje - datetime.timedelta(days=i) for i in range(aluno['ofensiva'])]
        dias_da_semana = [d for d in dias if d >= segunda]
        dias_antigos = [d for d in dias if d < segunda]

        def registrar(dia, quantidade, motivo):
            momento = agora - datetime.timedelta(days=(hoje - dia).days)
            RegistroXP.objects.create(user=user, quantidade=quantidade, motivo=motivo, criado_em=momento)

        # XP da semana dividido entre os dias desta semana
        if dias_da_semana:
            parte = aluno['xp_semana'] // len(dias_da_semana)
            for i, dia in enumerate(dias_da_semana):
                resto = aluno['xp_semana'] - parte * len(dias_da_semana) if i == 0 else 0
                registrar(dia, parte + resto, 'Lições e jogos')

        # Dias antigos da ofensiva: 10 XP cada; o restante do total fica num registro antigo
        for dia in dias_antigos:
            registrar(dia, 10, 'Lições e jogos')
        antigo = aluno['xp_total'] - aluno['xp_semana'] - 10 * len(dias_antigos)
        if antigo > 0:
            registrar(hoje - datetime.timedelta(days=aluno['ofensiva'] + 2), antigo, 'Semestre anterior')


def descarregar(apps, schema_editor):
    """Desfaz a carga (python manage.py migrate game 0002)."""
    for modelo in ['Materia', 'Afirmacao', 'Evento', 'Oportunidade']:
        apps.get_model('game', modelo).objects.all().delete()
    usernames = [a['username'] for a in D.ALUNOS_DEMO]
    apps.get_model('auth', 'User').objects.filter(username__in=usernames).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('game', '0002_estrutura_estudai'),
        ('auth', '__latest__'),
    ]

    operations = [
        migrations.RunPython(carregar, descarregar),
    ]
