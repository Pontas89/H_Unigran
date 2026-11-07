# Estudaí 🔥

Plataforma de estudos gamificada para alunos do ensino médio, inspirada na dinâmica do Duolingo: trilhas por matéria, jogos, XP, ofensiva, ranking e a **Fagulha**, uma IA de estudos (Google Gemini) que guia o aluno sem entregar respostas prontas.

> MVP desenvolvido no hackathon da Unigran (novembro/2026).

---

## Sumário

- [Funcionalidades](#funcionalidades)
- [Tecnologias](#tecnologias)
- [Como rodar](#como-rodar)
- [Configurando a Fagulha (Gemini)](#configurando-a-fagulha-gemini)
- [Perfis de acesso](#perfis-de-acesso)
- [Estrutura do projeto](#estrutura-do-projeto)
- [Rotas principais](#rotas-principais)
- [Banco de dados](#banco-de-dados)
- [Comandos úteis](#comandos-úteis)

---

## Funcionalidades

| Tela | O que faz |
|---|---|
| **Apresentação** | Página inicial pública com o resumo do projeto e os botões de entrar e cadastrar. |
| **Início** | Saudação, meta diária de XP, ofensiva, recompensa diária de 7 dias, aulas do dia, próximas provas, progresso nas matérias e mini ranking. |
| **Matérias** | Trilha de cada matéria em unidades e lições. As lições são liberadas uma a uma conforme o aluno conclui. |
| **Lição** | Quiz com 5 vidas. Ao terminar, a lição fica concluída e o aluno ganha XP. |
| **Jogos** | Quiz relâmpago, Verdadeiro ou falso (60 s), Memória de conceitos e Linha do tempo. |
| **Ranking** | Liga da semana (XP desde segunda-feira), XP total e ranking de turmas. |
| **Calendário** | Provas, simulados, entregas e eventos em 3 meses, com as aulas de cada dia. |
| **Oportunidades** | Eventos, cursos, estágios e concursos filtrados por categoria. |
| **Bem-estar** | Respiração guiada e contatos de apoio (escola, CVV 188, SAMU 192). |
| **Perfil** | Nível, XP, ofensiva, posição na liga, conquistas e progresso por matéria. |
| **Fagulha** | Chat de IA em todas as telas. Conhece o progresso, as provas e a página atual do aluno, e lembra o compromisso mais próximo da agenda. |

---

## Tecnologias

- **Python 3.14** + **Django 6.1**
- **uv** para gerenciar o ambiente e as dependências
- **SQLite** como banco de dados
- **django-jazzmin 3.0.1** para o visual do painel `/admin`
- **Tailwind CSS** (já compilado em `game/static/game/css/estudai.css`), **JavaScript puro** e ícones **Lucide**
- **Google Gemini** (API REST, sem bibliotecas extras) para a Fagulha

---

## Como rodar

**Pré-requisito:** ter o [uv](https://docs.astral.sh/uv/) instalado. O uv baixa o Python 3.14 sozinho, se precisar.

```powershell
# 1. Clonar o repositório
git clone https://github.com/Pontas89/H_Unigran.git
cd H_Unigran

# 2. Instalar as dependências (cria a pasta .venv)
uv sync

# 3. Criar/atualizar as tabelas do banco
uv run python manage.py migrate

# 4. Criar um administrador (se o banco for novo)
uv run python manage.py createsuperuser

# 5. Subir o servidor
uv run python manage.py runserver
```

Depois, abra **http://127.0.0.1:8000/**.

> **Windows: "uv não é reconhecido"?** O uv foi instalado numa pasta que não está no PATH. Rode uma vez o comando abaixo e reabra o terminal ou o VS Code:
>
> ```powershell
> [Environment]::SetEnvironmentVariable('Path', [Environment]::GetEnvironmentVariable('Path','User') + ";$env:APPDATA\Python\Python313\Scripts", 'User')
> ```

---

## Configurando a Fagulha (Gemini)

A Fagulha funciona **com ou sem** chave de API:

- **Sem chave:** responde com respostas prontas por palavra-chave.
- **Com chave:** usa o Gemini, com o contexto do aluno (nome, XP, progresso, provas e página atual).

1. Gere uma chave em https://aistudio.google.com/apikey.
2. Defina a chave **como variável de ambiente**, no mesmo terminal do `runserver`:

   ```powershell
   $env:GEMINI_API_KEY="sua-chave-aqui"
   uv run python manage.py runserver
   ```

3. Para ver o modelo em uso e os modelos que a sua chave pode usar:

   ```powershell
   uv run python manage.py gemini_modelos
   ```

> ⚠️ **Nunca escreva a chave dentro do `settings.py`.** Se ela for para o GitHub, o Google pode desativá-la.

| Variável | Padrão | Para que serve |
|---|---|---|
| `GEMINI_API_KEY` | vazio | Chave da API do Gemini |
| `GEMINI_MODEL` | `gemini-flash-latest` | Modelo principal (rápido, ideal para chat) |
| `GEMINI_MODEL_RESERVA` | `gemini-2.5-flash` | Usado automaticamente se o principal falhar |

O jeito da Fagulha (personalidade, regras de ensino e cuidados) fica em [`game/fagulha_contexto.py`](game/fagulha_contexto.py).

---

## Perfis de acesso

| Perfil | Como criar | O que pode fazer |
|---|---|---|
| **Administrador** | `createsuperuser` | Cadastrar, editar e excluir matérias (com unidades e lições), perguntas do quiz, afirmações do verdadeiro ou falso, eventos da agenda e oportunidades. Os botões aparecem nas próprias telas. Também acessa o `/admin`. Não aparece no ranking. |
| **Aluno** | Tela "Criar Conta" ou `/admin` → **Accounts → Alunos** | Jogar, fazer lições e registrar progresso: XP, lições concluídas, ofensiva e ranking. Não acessa as telas de cadastro. |

---

## Estrutura do projeto

Organizada no padrão do projeto de referência [layout_3d](https://github.com/andreyferramentasia/layout_3d):

```
H_Unigran/
├── app/                      Configuração do Django (settings.py e urls.py)
├── accounts/                 Acesso: apresentação, entrar, sair e criar conta
│   ├── static/accounts/css/  Visual das telas de acesso (vindo de escola_futuro/)
│   └── templates/accounts/
├── game/                     O sistema em si
│   ├── models.py             Matéria > Unidade > Lição, quiz, perfil, XP, agenda...
│   ├── servicos.py           Regras de negócio em classes (progresso, ranking, calendário, recompensa)
│   ├── views.py              Telas do aluno, API do app.js e CRUDs do admin
│   ├── forms.py              Formulários do admin
│   ├── fagulha.py            Conversa com a API do Gemini
│   ├── fagulha_contexto.py   Personalidade e contexto da Fagulha
│   ├── dados_iniciais.py     Dados de exemplo (carregados pela migration 0003)
│   ├── management/commands/  Comando gemini_modelos
│   ├── static/game/          CSS, JavaScript (app.js), imagens e fontes
│   └── templates/game/       Telas do sistema (+ admin/ com as telas de cadastro)
├── templates/                base.html e partials (menu, topo, menu do celular, Fagulha)
├── escola_futuro/            Protótipo HTML/CSS das telas de acesso (referência de design)
└── manage.py
```

**Como as partes conversam:**

```
Navegador ──> urls.py ──> views.py ──> servicos.py ──> models.py ──> banco
                             │
                             └──> templates (HTML) + app.js
app.js ──(fetch JSON)──> /game/api/...  (XP, lição concluída, recompensa, Fagulha)
```

---

## Rotas principais

| URL | Tela |
|---|---|
| `/` | Apresentação (quem já entrou vai para o início) |
| `/accounts/login/` · `/accounts/register/` | Entrar · Criar conta |
| `/game/inicio/` | Início |
| `/game/materias/` · `/game/materias/<slug>/` | Matérias · Trilha da matéria |
| `/game/licoes/<id>/` | Lição (quiz) |
| `/game/jogos/` | Jogos |
| `/game/ranking/` · `/game/calendario/` · `/game/oportunidades/` | Ranking · Calendário · Oportunidades |
| `/game/bem-estar/` · `/game/perfil/` | Bem-estar · Perfil |
| `/game/admin/materias/` · `/game/admin/quiz/` · `/game/admin/verdadeiro-falso/` | Cadastros (só admin) |
| `/admin/` | Painel do Django (Jazzmin) |

---

## Banco de dados

- **`game/migrations/0003_carga_inicial.py`:** num banco **novo**, preenche matérias, trilhas, perguntas, afirmações, agenda, oportunidades e 11 colegas de demonstração para o ranking. Os dados ficam em [`game/dados_iniciais.py`](game/dados_iniciais.py).
- **`accounts/migrations/0002_aluno_remove_account.py`:** troca o model antigo `Account` pelo `Aluno` (proxy do `User` do Django) e converte as contas antigas em usuários que conseguem fazer login.
- O **horário de aulas** do calendário é fixo, em `AULAS_POR_DIA_DA_SEMANA` (`game/dados_iniciais.py`).

---

## Comandos úteis

```powershell
uv run python manage.py runserver        # sobe o sistema
uv run python manage.py migrate          # aplica as migrations
uv run python manage.py createsuperuser  # cria um administrador
uv run python manage.py gemini_modelos   # mostra o modelo do Gemini em uso
uv run python manage.py check            # verifica a configuração
uv add <pacote>                          # instala uma dependência nova
```
