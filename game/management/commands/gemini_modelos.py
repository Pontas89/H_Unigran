"""Mostra o modelo do Gemini configurado e lista os modelos que a chave pode usar.

Uso: uv run python manage.py gemini_modelos
"""
import json
import urllib.error
import urllib.request

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = 'Lista os modelos do Gemini disponíveis para a GEMINI_API_KEY configurada.'

    def handle(self, *args, **options):
        if not settings.GEMINI_API_KEY:
            raise CommandError('GEMINI_API_KEY vazia: defina a variável de ambiente ou cole no app/settings.py.')

        reserva = getattr(settings, 'GEMINI_MODEL_RESERVA', '')
        self.stdout.write(f'Modelo principal (GEMINI_MODEL): {settings.GEMINI_MODEL}')
        self.stdout.write(f'Modelo reserva (GEMINI_MODEL_RESERVA): {reserva or "nenhum"}\n')

        requisicao = urllib.request.Request(
            'https://generativelanguage.googleapis.com/v1beta/models?pageSize=1000',
            headers={'x-goog-api-key': settings.GEMINI_API_KEY},
        )
        try:
            with urllib.request.urlopen(requisicao, timeout=30) as resposta:
                modelos = json.loads(resposta.read().decode('utf-8')).get('models', [])
        except urllib.error.HTTPError as erro:
            raise CommandError(f'Gemini respondeu {erro.code}: {erro.read().decode("utf-8", "ignore")[:300]}')
        except urllib.error.URLError as erro:
            raise CommandError(f'Sem conexão com o Gemini: {erro}')

        chat = [m for m in modelos if 'generateContent' in m.get('supportedGenerationMethods', [])]
        nomes = sorted(m['name'].removeprefix('models/') for m in chat)
        self.stdout.write('Modelos que sua chave pode usar no chat:')
        for nome in nomes:
            marca = '  <-- em uso' if nome == settings.GEMINI_MODEL else ('  <-- reserva' if nome == reserva else '')
            self.stdout.write(f'  • {nome}{marca}')

        if reserva and reserva not in nomes:
            self.stdout.write(self.style.WARNING(f'\nATENÇÃO: a reserva "{reserva}" não está na lista.'))
        if settings.GEMINI_MODEL not in nomes:
            self.stdout.write(self.style.WARNING(
                f'\nATENÇÃO: "{settings.GEMINI_MODEL}" não está na lista. '
                'Troque GEMINI_MODEL no settings.py por um dos nomes acima.'))
        else:
            self.stdout.write(self.style.SUCCESS(f'\nTudo certo: a Fagulha vai usar {settings.GEMINI_MODEL}.'))
