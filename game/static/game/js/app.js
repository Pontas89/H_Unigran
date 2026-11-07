/* =====================================================================
   ESTUDAÍ — JavaScript da plataforma
   Cada parte abaixo cuida de UMA coisa e só roda se a página tiver
   aquele elemento. Ex.: o código do quiz só roda na página da lição.
   ===================================================================== */

// Atalho para pegar um elemento pelo id
function pegar(id) {
  return document.getElementById(id)
}

// Mostra os ícones (biblioteca Lucide transforma <i data-lucide="..."> em desenho)
function atualizarIcones() {
  lucide.createIcons()
}

/* ---------------------------------------------------------------------
   1. MODO ESCURO
   Coloca ou tira a classe "dark" no <html> e guarda a escolha.
   --------------------------------------------------------------------- */
if (localStorage.getItem('tema') === 'escuro') {
  document.documentElement.classList.add('dark')
}

document.querySelectorAll('.botao-tema').forEach(function (botao) {
  botao.addEventListener('click', function () {
    document.documentElement.classList.toggle('dark')
    const escuro = document.documentElement.classList.contains('dark')
    localStorage.setItem('tema', escuro ? 'escuro' : 'claro')
  })
})

/* ---------------------------------------------------------------------
   2. MENU DO CELULAR (abrir e fechar)
   --------------------------------------------------------------------- */
if (pegar('menu-abrir')) {
  pegar('menu-abrir').addEventListener('click', function () {
    pegar('menu-celular').hidden = false
  })
  document.querySelectorAll('.menu-fechar').forEach(function (botao) {
    botao.addEventListener('click', function () {
      pegar('menu-celular').hidden = true
    })
  })
}

/* ---------------------------------------------------------------------
   3. XP E AVISOS
   O XP fica salvo no servidor (Django). O topo mostra o valor que veio do banco.
   --------------------------------------------------------------------- */
let xpTotal = pegar('xp-total') ? Number(pegar('xp-total').dataset.xp) : 0

function mostrarXP() {
  if (pegar('xp-total')) {
    pegar('xp-total').textContent = xpTotal.toLocaleString('pt-BR')
  }
}
mostrarXP()

// Envia dados para uma URL do Django (POST com JSON e o token CSRF)
function enviarParaServidor(url, dados) {
  return fetch(url, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-CSRFToken': document.querySelector('meta[name="csrf-token"]').content,
    },
    body: JSON.stringify(dados),
  }).then(function (resposta) {
    return resposta.ok ? resposta.json() : Promise.reject(resposta.status)
  })
}

// Atualiza o topo com o que o servidor devolveu (XP total e ofensiva)
function atualizarTopo(dados) {
  xpTotal = dados.xp_total
  mostrarXP()
  if (pegar('ofensiva-total')) pegar('ofensiva-total').textContent = dados.ofensiva
}

// Mostra um aviso laranja no topo da tela por 3 segundos
function mostrarAviso(titulo, texto) {
  const aviso = document.createElement('div')
  aviso.className = 'animate-pop-in flex items-center gap-3 rounded-2xl bg-primary px-5 py-3 text-primary-foreground btn-3d'
  aviso.innerHTML = '<span class="flex flex-col"><span class="font-black">' + titulo + '</span>' +
    '<span class="text-sm font-semibold opacity-90">' + texto + '</span></span>'
  pegar('avisos').appendChild(aviso)
  setTimeout(function () { aviso.remove() }, 3000)
}

// Soma XP na tela, avisa o aluno e salva no servidor
//   salvar = false quando outra chamada já salvou (ex.: lição concluída)
function ganharXP(quantidade, motivo, salvar) {
  xpTotal = xpTotal + quantidade
  mostrarXP()
  mostrarAviso('+' + quantidade + ' XP', motivo)

  if (salvar !== false) {
    enviarParaServidor(document.body.dataset.urlXp, { quantidade: quantidade, motivo: motivo })
      .then(atualizarTopo)
      .catch(function () { mostrarAviso('Ops!', 'Não deu para salvar seu XP agora.') })
  }
}

/* ---------------------------------------------------------------------
   4. INÍCIO: saudação e recompensa diária
   --------------------------------------------------------------------- */
if (pegar('saudacao')) {
  const hora = new Date().getHours()
  if (hora < 12) pegar('saudacao').textContent = 'Bom dia'
  else if (hora < 18) pegar('saudacao').textContent = 'Boa tarde'
  else pegar('saudacao').textContent = 'Boa noite'
}

// Recompensa diária: o servidor decide o XP do dia (game/servicos.py → RecompensaDiaria)
if (pegar('botao-recompensa')) {
  const botao = pegar('botao-recompensa')

  botao.addEventListener('click', function () {
    botao.disabled = true
    enviarParaServidor(botao.dataset.url, {})
      .then(function (dados) {
        atualizarTopo(dados)
        mostrarAviso('+' + dados.xp + ' XP', 'Recompensa diária')
        botao.textContent = 'Volte amanhã'
        // pinta o quadradinho de hoje como resgatado
        pegar('recompensa-hoje').className =
          'flex flex-col items-center gap-1 rounded-xl border-2 border-primary bg-primary py-2 text-primary-foreground'
      })
      .catch(function () {
        botao.textContent = 'Volte amanhã'
      })
  })
}

/* ---------------------------------------------------------------------
   5. FAGULHA (a IA de estudos)
   Com GEMINI_API_KEY no settings.py, as respostas vêm do Gemini (view game:fagulha).
   Sem chave, usa as respostas prontas de responderFagulha().
   --------------------------------------------------------------------- */
const respostasFagulha = [
  {
    palavras: ['mal', 'triste', 'ansios', 'estress', 'sentindo'],
    resposta: 'Obrigada por me contar como você está. Tudo bem não estar 100%.\n\n' +
      '• Escolha uma tarefa pequena para hoje\n• Estude 25 minutos e pause 5\n• Use a respiração guiada na aba Bem-estar\n\n' +
      'Se estiver pesado demais, fale com a psicóloga da escola ou ligue 188 (CVV), 24h e de graça.',
  },
  {
    palavras: ['x²', 'equação', 'resolva', 'bhaskara'],
    resposta: 'Bora resolver x² − 5x + 6 = 0 passo a passo!\n\n' +
      '1) Coeficientes: a = 1, b = −5, c = 6\n2) Delta: Δ = 25 − 24 = 1\n3) Bhaskara: x = (5 ± 1) / 2\n\n' +
      'Então x = 3 ou x = 2. Agora tente sozinha: x² − 7x + 10 = 0',
  },
  {
    palavras: ['simulado'],
    resposta: 'Mini simulado! Responda antes de ver o gabarito:\n\n' +
      '1) Raiz de f(x) = 3x − 12?  A) 3  B) 4  C) 12\n2) PA com a₁ = 5 e r = 2. Qual o 6º termo?  A) 13  B) 15  C) 17\n3) sen(30°) vale:  A) 1  B) √3/2  C) 1/2\n\n' +
      'Gabarito: 1-B, 2-B, 3-C',
  },
  {
    palavras: ['fotoss'],
    resposta: 'Pensa na planta como uma cozinha solar 🌱\n\n' +
      '• Ingredientes: água, gás carbônico e luz do sol\n• Onde: nos cloroplastos (clorofila)\n• Resultado: glicose (energia) e oxigênio\n\n' +
      'Pergunta rápida: por que isso é importante para nós?',
  },
  {
    palavras: ['revis', 'prova', 'química'],
    resposta: 'Plano de revisão em 3 dias:\n\n' +
      '• Dia 1: conceitos principais + 5 exercícios\n• Dia 2: resumo em flashcards\n• Dia 3: mini simulado e revisar só o que errou\n\n' +
      'Quer que eu comece com 3 perguntas?',
  },
]

function responderFagulha(pergunta) {
  const texto = pergunta.toLowerCase()
  for (const item of respostasFagulha) {
    for (const palavra of item.palavras) {
      if (texto.includes(palavra)) return item.resposta
    }
  }
  return 'Boa pergunta! Posso explicar o conteúdo, resolver uma questão passo a passo ou montar um simulado. Me conta a matéria e o assunto. 🔥'
}

// Coloca um balão de mensagem no chat
function adicionarMensagem(texto, deQuem) {
  const balao = document.createElement('div')
  if (deQuem === 'aluno') {
    balao.className = 'ml-auto max-w-[88%] whitespace-pre-line rounded-2xl bg-primary px-4 py-2.5 text-sm leading-relaxed text-primary-foreground'
  } else {
    balao.className = 'max-w-[88%] whitespace-pre-line rounded-2xl bg-muted px-4 py-2.5 text-sm leading-relaxed text-foreground'
  }
  balao.textContent = texto
  pegar('fagulha-mensagens').appendChild(balao)
  pegar('fagulha-mensagens').scrollTop = pegar('fagulha-mensagens').scrollHeight
}

// Conversa guardada para a IA lembrar do contexto
const historicoFagulha = []

function enviarParaFagulha(texto) {
  if (texto.trim() === '') return
  pegar('fagulha-sugestoes').hidden = true
  adicionarMensagem(texto, 'aluno')
  historicoFagulha.push({ autor: 'aluno', texto: texto })

  adicionarMensagem('Pensando…', 'fagulha')
  const balao = pegar('fagulha-mensagens').lastElementChild

  function responder(resposta) {
    balao.textContent = resposta
    historicoFagulha.push({ autor: 'fagulha', texto: resposta })
    pegar('fagulha-mensagens').scrollTop = pegar('fagulha-mensagens').scrollHeight
  }

  // Pergunta ao Django, que chama o Gemini. Se não tiver chave ou der erro, usa as respostas prontas.
  enviarParaServidor(pegar('fagulha-form').dataset.url, { historico: historicoFagulha, pagina: document.title })
    .then(function (dados) {
      console.log('Fagulha respondeu com o modelo:', dados.modelo)
      responder(dados.resposta)
    })
    .catch(function () { responder(responderFagulha(texto)) })
}

function abrirFagulha(pergunta) {
  pegar('fagulha-chat').hidden = false
  pegar('fagulha-botoes').hidden = true
  if (pergunta) enviarParaFagulha(pergunta)
}

if (pegar('fagulha-chat')) {
  // Qualquer botão com data-fagulha abre o chat (e já manda a pergunta, se tiver)
  document.querySelectorAll('[data-fagulha]').forEach(function (botao) {
    botao.addEventListener('click', function () {
      abrirFagulha(botao.dataset.fagulha)
    })
  })

  pegar('fagulha-fechar').addEventListener('click', function () {
    pegar('fagulha-chat').hidden = true
    pegar('fagulha-botoes').hidden = false
  })

  document.querySelectorAll('.sugestao').forEach(function (botao) {
    botao.addEventListener('click', function () {
      enviarParaFagulha(botao.textContent)
    })
  })

  pegar('fagulha-form').addEventListener('submit', function (evento) {
    evento.preventDefault() // não recarrega a página
    enviarParaFagulha(pegar('fagulha-input').value)
    pegar('fagulha-input').value = ''
  })

  // Lembrete (só existe se houver compromisso próximo na agenda)
  // Aparece 4 segundos depois de abrir a página e, se fechar, não volta mais hoje.
  const lembrete = pegar('fagulha-lembrete')
  const chaveLembrete = 'lembrete-fechado-' + new Date().toDateString()

  if (lembrete && !sessionStorage.getItem(chaveLembrete)) {
    setTimeout(function () { lembrete.hidden = false }, 4000)
    pegar('fagulha-lembrete-fechar').addEventListener('click', function () {
      lembrete.hidden = true
      sessionStorage.setItem(chaveLembrete, 'sim')
    })
  }
}

/* ---------------------------------------------------------------------
   6. ABAS DO RANKING
   Cada botão tem data-aba e cada conteúdo tem data-conteudo com o mesmo nome.
   --------------------------------------------------------------------- */
document.querySelectorAll('[data-aba]').forEach(function (botao) {
  botao.addEventListener('click', function () {
    // mostra só o conteúdo da aba clicada
    document.querySelectorAll('[data-conteudo]').forEach(function (conteudo) {
      conteudo.hidden = conteudo.dataset.conteudo !== botao.dataset.aba
    })
    // pinta só o botão clicado
    document.querySelectorAll('[data-aba]').forEach(function (b) {
      b.classList.remove('border-primary', 'bg-accent', 'text-accent-foreground')
      b.classList.add('border-border', 'text-muted-foreground')
    })
    botao.classList.add('border-primary', 'bg-accent', 'text-accent-foreground')
    botao.classList.remove('border-border', 'text-muted-foreground')
  })
})

/* ---------------------------------------------------------------------
   7. OPORTUNIDADES: filtrar por categoria e salvar
   --------------------------------------------------------------------- */
document.querySelectorAll('[data-categoria]').forEach(function (botao) {
  botao.addEventListener('click', function () {
    document.querySelectorAll('[data-card]').forEach(function (card) {
      card.hidden = card.dataset.card !== botao.dataset.categoria
    })
    document.querySelectorAll('[data-categoria]').forEach(function (b) {
      b.classList.remove('border-primary', 'bg-primary', 'text-primary-foreground', 'btn-3d')
      b.classList.add('border-border', 'btn-3d-muted')
    })
    botao.classList.add('border-primary', 'bg-primary', 'text-primary-foreground', 'btn-3d')
    botao.classList.remove('border-border', 'btn-3d-muted')
  })
})

document.querySelectorAll('.salvar').forEach(function (botao) {
  botao.addEventListener('click', function () {
    const salvo = botao.classList.toggle('text-primary')
    botao.querySelector('svg').setAttribute('fill', salvo ? 'currentColor' : 'none')
  })
})

/* ---------------------------------------------------------------------
   8. CALENDÁRIO: escolher um dia e trocar de mês
   --------------------------------------------------------------------- */
if (pegar('mes-titulo')) {
  document.querySelectorAll('.dia').forEach(function (botao) {
    botao.addEventListener('click', function () {
      const dia = botao.dataset.dia
      let achou = false
      // destaca o dia escolhido na grade do mês
      document.querySelectorAll('[data-mes] .dia').forEach(function (d) {
        const escolhido = d.dataset.dia === dia
        d.classList.toggle('border-primary', escolhido)
        d.classList.toggle('bg-accent', escolhido)
        d.classList.toggle('border-transparent', !escolhido)
      })
      // mostra o detalhe do dia escolhido
      document.querySelectorAll('[data-detalhe]').forEach(function (painel) {
        painel.hidden = painel.dataset.detalhe !== dia
        if (!painel.hidden) achou = true
      })
      // se o dia não tem nada, mostra o painel "vazio" com a data
      if (!achou) {
        const data = new Date(dia + 'T12:00')
        pegar('vazio-titulo').textContent = data.toLocaleDateString('pt-BR', { weekday: 'long', day: 'numeric', month: 'long' })
        document.querySelector('[data-detalhe="vazio"]').hidden = false
        // (admin) o botão "Adicionar neste dia" já leva a data escolhida
        if (pegar('vazio-adicionar')) {
          pegar('vazio-adicionar').href = pegar('vazio-adicionar').dataset.base + '?data=' + dia
        }
      }
    })
  })

  // Troca de mês: o Django manda 3 meses prontos (<div data-mes="2026-11" data-nome="...">)
  const meses = Array.from(document.querySelectorAll('[data-mes]'))
  let mesAtual = 0

  function mostrarMes(indice) {
    mesAtual = Math.max(0, Math.min(meses.length - 1, indice)) // não passa do primeiro nem do último
    meses.forEach(function (grade, i) { grade.hidden = i !== mesAtual })
    pegar('mes-titulo').textContent = meses[mesAtual].dataset.nome
  }

  pegar('mes-anterior').addEventListener('click', function () { mostrarMes(mesAtual - 1) })
  pegar('mes-proximo').addEventListener('click', function () { mostrarMes(mesAtual + 1) })
}

/* ---------------------------------------------------------------------
   9. BEM-ESTAR: respiração guiada
   --------------------------------------------------------------------- */
if (pegar('respiracao-botao')) {
  // As 3 etapas da respiração: nome, segundos e tamanho do círculo
  const etapas = [
    { nome: 'Inspire', segundos: 4, tamanho: 1 },
    { nome: 'Segure', segundos: 4, tamanho: 1 },
    { nome: 'Expire', segundos: 6, tamanho: 0.55 },
  ]
  let relogio = null
  let etapa = 0
  let contador = 0

  function mostrarEtapa() {
    const atual = etapas[etapa]
    contador = atual.segundos
    pegar('respiracao-texto').textContent = atual.nome
    pegar('respiracao-contador').textContent = contador
    pegar('circulo').style.transitionDuration = atual.segundos + 's'
    pegar('circulo').style.transform = 'scale(' + atual.tamanho + ')'
  }

  pegar('respiracao-botao').addEventListener('click', function () {
    if (relogio) {
      // PARAR
      clearInterval(relogio)
      relogio = null
      pegar('respiracao-texto').textContent = 'Pronto?'
      pegar('respiracao-contador').textContent = ''
      pegar('circulo').style.transform = 'scale(0.7)'
      pegar('respiracao-botao').textContent = 'Começar'
      return
    }
    // COMEÇAR
    etapa = 0
    mostrarEtapa()
    pegar('respiracao-botao').textContent = 'Parar'
    relogio = setInterval(function () {
      contador = contador - 1
      if (contador > 0) {
        pegar('respiracao-contador').textContent = contador
      } else {
        etapa = (etapa + 1) % etapas.length // volta para a 1ª etapa no final
        mostrarEtapa()
      }
    }, 1000)
  })
}

/* ---------------------------------------------------------------------
   10. LIÇÃO (QUIZ)
   As perguntas vêm do Django (cadastradas pelo admin), dentro do <script id="dados-licao">.
   --------------------------------------------------------------------- */
if (pegar('tela-quiz')) {
  const licao = JSON.parse(pegar('dados-licao').textContent)
  const urlConcluir = pegar('tela-quiz').dataset.urlConcluir // só existe nas lições da trilha
  let numero = 0      // qual pergunta está na tela
  let escolhida = null // alternativa clicada
  let acertos = 0
  let vidas = 5
  let jaVerificou = false

  pegar('titulo-licao').textContent = licao.titulo

  // Sem perguntas cadastradas: avisa e não quebra a tela
  if (licao.perguntas.length === 0) {
    pegar('pergunta').textContent = 'Ainda não há perguntas cadastradas para esta lição.'
    pegar('botao-verificar').hidden = true
  }

  function mostrarPergunta() {
    const p = licao.perguntas[numero]
    escolhida = null
    jaVerificou = false
    pegar('pergunta').textContent = p.pergunta
    pegar('barra-progresso').style.width = Math.max(4, (numero / licao.perguntas.length) * 100) + '%'
    pegar('rodape').className = 'border-t-2 border-border px-4 py-6'
    pegar('feedback').innerHTML = ''
    pegar('botao-verificar').textContent = 'Verificar'
    pegar('botao-verificar').disabled = true
    pegar('botao-verificar').classList.replace('bg-destructive', 'bg-primary') // volta a ser laranja

    // cria um botão para cada alternativa
    pegar('alternativas').innerHTML = ''
    p.alternativas.forEach(function (texto, indice) {
      const botao = document.createElement('button')
      botao.type = 'button'
      botao.className = 'alternativa flex items-center gap-4 rounded-2xl border-2 border-border bg-card px-4 py-4 text-left text-lg font-bold btn-3d-muted transition-colors hover:bg-muted'
      botao.innerHTML = '<span class="flex size-8 shrink-0 items-center justify-center rounded-lg border-2 border-current text-sm font-black opacity-70">' +
        (indice + 1) + '</span>'
      botao.append(texto)
      botao.addEventListener('click', function () { escolher(indice) })
      pegar('alternativas').appendChild(botao)
    })
  }

  function escolher(indice) {
    if (jaVerificou) return
    escolhida = indice
    document.querySelectorAll('.alternativa').forEach(function (botao, i) {
      botao.classList.toggle('border-primary', i === indice)
      botao.classList.toggle('bg-accent', i === indice)
    })
    pegar('botao-verificar').disabled = false
  }

  function verificar() {
    const p = licao.perguntas[numero]
    const acertou = escolhida === p.correta
    jaVerificou = true
    pegar('barra-progresso').style.width = ((numero + 1) / licao.perguntas.length) * 100 + '%'

    // pinta a certa de laranja e a errada de vermelho
    const botoes = document.querySelectorAll('.alternativa')
    botoes.forEach(function (b) { b.classList.add('opacity-60') })
    botoes[p.correta].classList.remove('opacity-60')
    botoes[p.correta].classList.add('border-primary', 'bg-accent', 'text-accent-foreground')
    if (!acertou) {
      botoes[escolhida].classList.remove('opacity-60', 'border-primary', 'bg-accent')
      botoes[escolhida].classList.add('border-destructive', 'bg-destructive/10', 'text-destructive')
    }

    if (acertou) {
      acertos = acertos + 1
      pegar('rodape').className = 'border-t-2 border-transparent bg-accent px-4 py-6'
      pegar('feedback').innerHTML = '<div><p class="text-xl font-black text-accent-foreground">Mandou bem!</p>' +
        '<p class="text-pretty font-semibold leading-relaxed">' + p.explicacao + '</p></div>'
    } else {
      vidas = vidas - 1
      pegar('vidas').textContent = vidas
      pegar('botao-verificar').classList.replace('bg-primary', 'bg-destructive') // botão fica vermelho
      pegar('rodape').className = 'border-t-2 border-transparent bg-destructive/10 px-4 py-6'
      pegar('feedback').innerHTML = '<div><p class="text-xl font-black text-destructive">Resposta: ' + p.alternativas[p.correta] + '</p>' +
        '<p class="text-pretty font-semibold leading-relaxed">' + p.explicacao + '</p></div>'
    }
    pegar('botao-verificar').textContent = 'Continuar'
  }

  function terminar() {
    const total = licao.perguntas.length
    let xp = acertos * 10
    if (acertos === total) xp = xp + 15 // bônus por gabaritar
    pegar('tela-quiz').hidden = true
    pegar('tela-final').hidden = false
    pegar('xp-ganho').textContent = xp
    pegar('precisao').textContent = Math.round((acertos / total) * 100) + '%'
    const motivo = licao.titulo + ': ' + acertos + '/' + total + ' acertos'

    if (urlConcluir) {
      // Lição da trilha: o servidor marca a lição como concluída e já salva o XP
      enviarParaServidor(urlConcluir, { acertos: acertos, total: total, xp: xp }).then(atualizarTopo)
      if (xp > 0) ganharXP(xp, motivo, false)
    } else if (xp > 0) {
      // Quiz relâmpago: só ganha XP
      ganharXP(xp, motivo)
    }
  }

  // O mesmo botão faz duas coisas: "Verificar" e depois "Continuar"
  pegar('botao-verificar').addEventListener('click', function () {
    if (!jaVerificou) {
      verificar()
    } else if (numero + 1 < licao.perguntas.length) {
      numero = numero + 1
      mostrarPergunta()
    } else {
      terminar()
    }
  })

  if (licao.perguntas.length > 0) mostrarPergunta()
}

/* ---------------------------------------------------------------------
   11. JOGO: VERDADEIRO OU FALSO (60 segundos)
   --------------------------------------------------------------------- */
if (pegar('vf-jogo')) {
  // Afirmações cadastradas pelo admin (vêm do Django dentro do <script id="dados-vf">)
  const afirmacoes = JSON.parse(pegar('dados-vf').textContent)
  let tempo = 60
  let pontos = 0
  let combo = 0
  let posicao = 0
  let relogioVF = null

  function mostrarAfirmacao() {
    if (afirmacoes.length === 0) {
      pegar('vf-frase').textContent = 'Nenhuma afirmação cadastrada ainda.'
      return
    }
    const item = afirmacoes[posicao % afirmacoes.length]
    pegar('vf-frase').textContent = item.frase
    pegar('vf-materia').textContent = item.materia
  }

  function comecarVF() {
    tempo = 60; pontos = 0; combo = 0
    posicao = Math.floor(Math.random() * afirmacoes.length) // começa num lugar aleatório
    pegar('vf-pontos').textContent = 0
    pegar('vf-combo').textContent = 0
    pegar('vf-tempo').textContent = 60
    pegar('vf-barra').style.width = '100%'
    pegar('vf-inicio').hidden = true
    pegar('vf-fim').hidden = true
    pegar('vf-jogo').hidden = false
    mostrarAfirmacao()

    relogioVF = setInterval(function () {
      tempo = tempo - 1
      pegar('vf-tempo').textContent = tempo
      pegar('vf-barra').style.width = (tempo / 60) * 100 + '%'
      if (tempo === 0) {
        clearInterval(relogioVF)
        pegar('vf-jogo').hidden = true
        pegar('vf-fim').hidden = false
        pegar('vf-total').textContent = pontos
      }
    }, 1000)
  }

  function responderVF(resposta) {
    if (afirmacoes.length === 0) return
    const item = afirmacoes[posicao % afirmacoes.length]
    const cartao = pegar('vf-cartao')
    if (item.resposta === resposta) {
      combo = combo + 1
      pontos = pontos + 5
      if (combo >= 3) pontos = pontos + 2 // bônus de combo
      cartao.classList.add('border-primary', 'bg-accent')
    } else {
      combo = 0
      cartao.classList.add('border-destructive', 'bg-destructive/10')
    }
    // tira a cor depois de um instante
    setTimeout(function () {
      cartao.classList.remove('border-primary', 'bg-accent', 'border-destructive', 'bg-destructive/10')
    }, 250)
    pegar('vf-pontos').textContent = pontos
    pegar('vf-combo').textContent = combo
    posicao = posicao + 1
    mostrarAfirmacao()
  }

  document.querySelectorAll('.vf-comecar').forEach(function (b) { b.addEventListener('click', comecarVF) })
  pegar('vf-verdadeiro').addEventListener('click', function () { responderVF(true) })
  pegar('vf-falso').addEventListener('click', function () { responderVF(false) })
  pegar('vf-resgatar').addEventListener('click', function () {
    if (pontos > 0) ganharXP(pontos, 'Verdadeiro ou falso')
    pegar('vf-resgatar').disabled = true
  })
}

/* ---------------------------------------------------------------------
   12. JOGO DA MEMÓRIA
   --------------------------------------------------------------------- */
if (pegar('memoria-jogo')) {
  let viradas = []   // cartas abertas na jogada atual (no máximo 2)
  let pares = 0
  let jogadas = 0

  function comecarMemoria() {
    pares = 0; jogadas = 0; viradas = []
    pegar('memoria-pares').textContent = 0
    pegar('memoria-jogadas').textContent = 0
    pegar('memoria-inicio').hidden = true
    pegar('memoria-fim').hidden = true
    pegar('memoria-jogo').hidden = false
    pegar('memoria-resgatar').disabled = false

    // monta as 12 cartas (termo + significado) e embaralha
    let cartas = []
    paresMemoria.forEach(function (par, numeroDoPar) {
      cartas.push({ texto: par.termo, par: numeroDoPar })
      cartas.push({ texto: par.significado, par: numeroDoPar })
    })
    cartas.sort(function () { return Math.random() - 0.5 })

    pegar('memoria-cartas').innerHTML = ''
    cartas.forEach(function (carta) {
      const botao = document.createElement('button')
      botao.type = 'button'
      botao.className = 'carta flex aspect-square w-full items-center justify-center rounded-2xl border-2 border-primary bg-primary p-2 text-center text-sm font-black text-primary-foreground btn-3d transition-all sm:text-base'
      botao.textContent = '?'
      botao.dataset.texto = carta.texto
      botao.dataset.par = carta.par
      botao.addEventListener('click', function () { virarCarta(botao) })
      const item = document.createElement('li')
      item.appendChild(botao)
      pegar('memoria-cartas').appendChild(item)
    })
  }

  function abrir(carta) {
    carta.textContent = carta.dataset.texto
    carta.classList.remove('bg-primary', 'text-primary-foreground', 'btn-3d')
    carta.classList.add('bg-card')
  }
  function fechar(carta) {
    carta.textContent = '?'
    carta.classList.add('bg-primary', 'text-primary-foreground', 'btn-3d')
    carta.classList.remove('bg-card')
  }

  function virarCarta(carta) {
    // não deixa virar mais de 2, nem a mesma carta, nem carta já acertada
    if (viradas.length === 2 || viradas.includes(carta) || carta.dataset.acertou) return
    abrir(carta)
    viradas.push(carta)
    if (viradas.length < 2) return

    jogadas = jogadas + 1
    pegar('memoria-jogadas').textContent = jogadas
    const [a, b] = viradas
    if (a.dataset.par === b.dataset.par) {
      // ACERTOU o par
      a.dataset.acertou = 'sim'; b.dataset.acertou = 'sim'
      a.className = b.className = 'carta flex aspect-square w-full items-center justify-center rounded-2xl border-2 border-border bg-accent p-2 text-center text-sm font-black text-accent-foreground sm:text-base'
      viradas = []
      pares = pares + 1
      pegar('memoria-pares').textContent = pares
      if (pares === paresMemoria.length) pegar('memoria-fim').hidden = false
    } else {
      // ERROU: espera um pouco e desvira
      setTimeout(function () { fechar(a); fechar(b); viradas = [] }, 900)
    }
  }

  document.querySelectorAll('.memoria-comecar').forEach(function (b) { b.addEventListener('click', comecarMemoria) })
  pegar('memoria-resgatar').addEventListener('click', function () {
    const xp = Math.max(20, 60 - Math.max(0, jogadas - 6) * 4) // menos jogadas = mais XP
    ganharXP(xp, 'Memória de conceitos')
    pegar('memoria-resgatar').disabled = true
  })
}

/* ---------------------------------------------------------------------
   13. JOGO: LINHA DO TEMPO (ordenar com as setas)
   --------------------------------------------------------------------- */
if (pegar('linha-lista')) {
  const lista = pegar('linha-lista')

  lista.addEventListener('click', function (evento) {
    const item = evento.target.closest('li')
    if (evento.target.closest('.subir') && item.previousElementSibling) {
      lista.insertBefore(item, item.previousElementSibling) // troca com o de cima
    }
    if (evento.target.closest('.descer') && item.nextElementSibling) {
      lista.insertBefore(item.nextElementSibling, item) // troca com o de baixo
    }
  })

  pegar('linha-verificar').addEventListener('click', function () {
    const itens = document.querySelectorAll('.item-linha')
    const anos = Array.from(itens).map(function (i) { return Number(i.dataset.ano) })
    const anosEmOrdem = anos.slice().sort(function (a, b) { return a - b })
    let certos = 0

    itens.forEach(function (item, i) {
      item.querySelector('.ano').classList.remove('hidden') // mostra o ano
      item.classList.remove('border-border', 'border-primary', 'bg-accent', 'border-destructive', 'bg-destructive/10')
      if (anos[i] === anosEmOrdem[i]) {
        certos = certos + 1
        item.classList.add('border-primary', 'bg-accent')
      } else {
        item.classList.add('border-destructive', 'bg-destructive/10')
      }
    })

    const resultado = pegar('linha-resultado')
    if (certos === itens.length) {
      resultado.className = 'text-center text-2xl font-black text-primary'
      resultado.textContent = 'Ordem perfeita! +40 XP'
      pegar('linha-verificar').disabled = true
      ganharXP(40, 'Linha do tempo')
    } else {
      resultado.className = 'text-center font-bold text-destructive'
      resultado.textContent = certos + ' de ' + itens.length + ' na posição certa. Ajuste e tente de novo!'
    }
  })
}

// Por último: desenha todos os ícones da página
atualizarIcones()
