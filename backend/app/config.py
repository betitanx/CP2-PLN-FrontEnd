import os
from pathlib import Path
from dotenv import load_dotenv

BASE = Path(__file__).resolve().parents[1]


class Config:
    def __init__(self):
        load_dotenv(BASE / '.env')
        self.api_key = os.getenv('API_KEY', '').strip()
        if not self.api_key:
            raise RuntimeError('Configure API_KEY no backend/.env antes de iniciar.')
        self.provider = os.getenv('LLM_PROVIDER', 'openrouter').strip()
        padroes = {
            'openrouter': ('google/gemma-4-26b-a4b-it:free', 'https://openrouter.ai/api/v1'),
            'ollama': ('qwen2.5:3b', 'http://localhost:11434'),
            'openai_compatible': ('', 'https://api.openai.com/v1'),
        }
        if self.provider not in padroes:
            raise RuntimeError('LLM_PROVIDER deve ser openrouter, ollama ou openai_compatible.')
        modelo_padrao, url_padrao = padroes[self.provider]
        self.model = os.getenv('LLM_MODEL', modelo_padrao).strip()
        self.url = os.getenv('LLM_URL', url_padrao).rstrip('/')
        variavel_chave = 'OPEN_ROUTER_KEY' if self.provider == 'openrouter' else 'LLM_API_KEY'
        self.llm_key = os.getenv(variavel_chave, '').strip()
        if not self.model:
            raise RuntimeError('Configure LLM_MODEL no backend/.env.')
        if self.provider == 'openrouter' and self.model != 'openrouter/free' and not self.model.endswith(':free'):
            raise RuntimeError('No OpenRouter, selecione um modelo gratuito com sufixo :free ou openrouter/free.')
        self.timeout = float(os.getenv('LLM_TIMEOUT', '60'))
        self.turns = max(1, int(os.getenv('CONTEXT_TURNS', '8')))
        caminho = Path(os.getenv('DATABASE_PATH', 'data/execucao/prosa.sqlite3'))
        self.database = caminho if caminho.is_absolute() else BASE / caminho
