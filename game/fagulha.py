"""Fagulha: conversa com a API do Gemini (só biblioteca padrão, sem dependências)."""
import json
import urllib.error
import urllib.request

from django.conf import settings

URL_GEMINI = 'https://generativelanguage.googleapis.com/v1beta/models/{modelo}:generateContent'


class FagulhaErro(Exception):
    pass


def gemini_configurado():
    return bool(settings.GEMINI_API_KEY)


def perguntar(historico, instrucoes):
    """Envia a conversa ao Gemini.

    historico: lista de {'autor': 'aluno'|'fagulha', 'texto': str}
    instrucoes: contexto/instrução de sistema (ver game/fagulha_contexto.py)
    Retorna (texto_da_resposta, modelo_que_respondeu).
    """
    conteudos = [
        {'role': 'user' if m['autor'] == 'aluno' else 'model', 'parts': [{'text': m['texto']}]}
        for m in historico
    ]
    corpo = {
        'system_instruction': {'parts': [{'text': instrucoes}]},
        'contents': conteudos,
    }
    modelos = [settings.GEMINI_MODEL]
    reserva = getattr(settings, 'GEMINI_MODEL_RESERVA', '')
    if reserva and reserva != settings.GEMINI_MODEL:
        modelos.append(reserva)

    ultimo_erro = None
    for modelo in modelos:
        try:
            dados = _chamar(modelo, corpo)
            break
        except FagulhaErro as erro:
            ultimo_erro = erro
            print(f'[Fagulha] modelo {modelo} falhou: {erro}', flush=True)
    else:
        raise ultimo_erro

    try:
        partes = dados['candidates'][0]['content']['parts']
        texto = ''.join(p.get('text', '') for p in partes if not p.get('thought')).strip()
    except (KeyError, IndexError) as erro:
        raise FagulhaErro(f'Resposta inesperada do Gemini: {str(dados)[:300]}') from erro
    if not texto:
        raise FagulhaErro(f'Gemini respondeu vazio: {str(dados)[:300]}')
    return texto, dados.get('modelVersion', modelo)


def _chamar(modelo, corpo):
    """Faz uma chamada ao generateContent de um modelo e devolve o JSON da resposta."""
    requisicao = urllib.request.Request(
        URL_GEMINI.format(modelo=modelo),
        data=json.dumps(corpo).encode('utf-8'),
        headers={'Content-Type': 'application/json', 'x-goog-api-key': settings.GEMINI_API_KEY},
        method='POST',
    )
    try:
        with urllib.request.urlopen(requisicao, timeout=60) as resposta:
            return json.loads(resposta.read().decode('utf-8'))
    except urllib.error.HTTPError as erro:
        raise FagulhaErro(f'Gemini respondeu {erro.code}: {erro.read().decode("utf-8", "ignore")[:300]}') from erro
    except (urllib.error.URLError, TimeoutError) as erro:
        raise FagulhaErro(f'Sem conexão com o Gemini: {erro}') from erro
