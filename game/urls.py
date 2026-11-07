from django.urls import path

from game import views

app_name = 'game'

urlpatterns = [
    # ------------------------------------------------------------ telas do aluno
    path('inicio/', views.InicioView.as_view(), name='inicio'),

    path('materias/', views.MateriaListView.as_view(), name='materia-list'),
    path('materias/<slug:slug>/', views.MateriaDetailView.as_view(), name='materia-detail'),
    path('licoes/<int:pk>/', views.LicaoView.as_view(), name='licao'),

    path('jogos/', views.JogoListView.as_view(), name='jogo-list'),
    path('jogos/quiz-relampago/', views.QuizRelampagoView.as_view(), name='quiz-relampago'),
    path('jogos/verdadeiro-falso/', views.JogoVerdadeiroFalsoView.as_view(), name='jogo-verdadeiro-falso'),
    path('jogos/memoria/', views.JogoMemoriaView.as_view(), name='jogo-memoria'),
    path('jogos/linha-do-tempo/', views.JogoLinhaDoTempoView.as_view(), name='jogo-linha-do-tempo'),

    path('ranking/', views.RankingView.as_view(), name='ranking'),
    path('calendario/', views.CalendarioView.as_view(), name='calendario'),
    path('oportunidades/', views.OportunidadesView.as_view(), name='oportunidades'),
    path('bem-estar/', views.BemEstarView.as_view(), name='bem-estar'),
    path('perfil/', views.PerfilView.as_view(), name='perfil'),

    # ------------------------------------------------------------ API (chamada pelo app.js)
    path('api/xp/', views.GanharXPView.as_view(), name='ganhar-xp'),
    path('api/licoes/<int:pk>/concluir/', views.ConcluirLicaoView.as_view(), name='licao-concluir'),
    path('api/recompensa/', views.RecompensaDiariaView.as_view(), name='recompensa-diaria'),
    path('fagulha/', views.FagulhaView.as_view(), name='fagulha'),

    # ------------------------------------------------------------ CRUDs do administrador
    # Matérias e unidades
    path('admin/materias/', views.MateriaGerenciarView.as_view(), name='materia-gerenciar'),
    path('admin/materias/nova/', views.MateriaCreateView.as_view(), name='materia-create'),
    path('admin/materias/<int:pk>/editar/', views.MateriaUpdateView.as_view(), name='materia-update'),
    path('admin/materias/<int:pk>/excluir/', views.MateriaDeleteView.as_view(), name='materia-delete'),
    path('admin/materias/<int:materia_pk>/unidades/nova/', views.UnidadeCreateView.as_view(), name='unidade-create'),
    path('admin/unidades/<int:pk>/editar/', views.UnidadeUpdateView.as_view(), name='unidade-update'),
    path('admin/unidades/<int:pk>/excluir/', views.UnidadeDeleteView.as_view(), name='unidade-delete'),

    # Quiz
    path('admin/quiz/', views.PerguntaListView.as_view(), name='pergunta-list'),
    path('admin/quiz/nova/', views.PerguntaCreateView.as_view(), name='pergunta-create'),
    path('admin/quiz/<int:pk>/editar/', views.PerguntaUpdateView.as_view(), name='pergunta-update'),
    path('admin/quiz/<int:pk>/excluir/', views.PerguntaDeleteView.as_view(), name='pergunta-delete'),

    # Verdadeiro ou falso
    path('admin/verdadeiro-falso/', views.AfirmacaoListView.as_view(), name='afirmacao-list'),
    path('admin/verdadeiro-falso/nova/', views.AfirmacaoCreateView.as_view(), name='afirmacao-create'),
    path('admin/verdadeiro-falso/<int:pk>/editar/', views.AfirmacaoUpdateView.as_view(), name='afirmacao-update'),
    path('admin/verdadeiro-falso/<int:pk>/excluir/', views.AfirmacaoDeleteView.as_view(), name='afirmacao-delete'),

    # Agenda
    path('admin/agenda/novo/', views.EventoCreateView.as_view(), name='evento-create'),
    path('admin/agenda/<int:pk>/editar/', views.EventoUpdateView.as_view(), name='evento-update'),
    path('admin/agenda/<int:pk>/excluir/', views.EventoDeleteView.as_view(), name='evento-delete'),

    # Oportunidades
    path('admin/oportunidades/nova/', views.OportunidadeCreateView.as_view(), name='oportunidade-create'),
    path('admin/oportunidades/<int:pk>/editar/', views.OportunidadeUpdateView.as_view(), name='oportunidade-update'),
    path('admin/oportunidades/<int:pk>/excluir/', views.OportunidadeDeleteView.as_view(), name='oportunidade-delete'),
]
