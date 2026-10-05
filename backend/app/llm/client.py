import json
import httpx
from pydantic import BaseModel, Field
from typing import Literal


class ModeloIndisponivel(Exception):
    pass


class Analise(BaseModel):
    intent: Literal['agendar','faq','humano','memoria','saudacao','agradecer','encerrar','cancelar','desconhecida']
    faq_id: str | None = None
    reply: str = Field(default='', max_length=4000)


class LLMClient:
    def __init__(self, config):
        self.config = config

    def disponivel(self):
        try:
            if self.config.provider == 'ollama':
                r = httpx.get(self.config.url + '/api/tags', timeout=2)
                r.raise_for_status()
                return any(m['name'] == self.config.model for m in r.json().get('models', []))
            if self.config.provider == 'openrouter':
                if not self.config.llm_key:
                    return False
                chave = httpx.get(self.config.url + '/key', headers={'Authorization': f'Bearer {self.config.llm_key}'}, timeout=2)
                chave.raise_for_status()
            r = httpx.get(self.config.url + '/models', headers={'Authorization': f'Bearer {self.config.llm_key}'}, timeout=2)
            r.raise_for_status()
            return any(m['id'] == self.config.model for m in r.json().get('data', []))
        except (httpx.HTTPError, ValueError, KeyError):
            return False

    def analisar(self, mensagens, model=None):
        return self.gerar_json(mensagens, model, Analise)

    def gerar_json(self, mensagens, model=None, esquema=Analise, limite=256):
        modelo = model or self.config.model
        if self.config.provider == 'openrouter' and modelo != 'openrouter/free' and not modelo.endswith(':free'):
            raise ModeloIndisponivel('Selecione um modelo gratuito do OpenRouter.')
        if self.config.provider == 'openrouter' and not self.config.llm_key:
            raise ModeloIndisponivel('Configure a chave do OpenRouter em OPEN_ROUTER_KEY no backend/.env. A conversa foi preservada.')
        try:
            if self.config.provider == 'ollama':
                r = httpx.post(self.config.url + '/api/chat', json={
                    'model': modelo, 'messages': mensagens,
                    'stream': False, 'format': esquema.model_json_schema(),
                    'options': {'temperature': 0, 'num_predict': limite},
                }, timeout=self.config.timeout)
                r.raise_for_status()
                conteudo = r.json()['message']['content']
            else:
                corpo = {'model': modelo, 'messages': mensagens,
                         'temperature': 0, 'max_tokens': limite, 'stream': False,
                         'response_format': {'type': 'json_object'}}
                if self.config.provider == 'openrouter':
                    if modelo in {'google/gemma-4-26b-a4b-it:free', 'nvidia/nemotron-3-super-120b-a12b:free'}:
                        corpo['reasoning'] = {'enabled': False}
                    # Seleciona endpoints compatíveis com JSON e preço zero.
                    corpo['provider'] = {'require_parameters': True,
                                         'max_price': {'prompt': 0, 'completion': 0, 'request': 0}}
                r = httpx.post(self.config.url + '/chat/completions', headers={
                    'Authorization': f'Bearer {self.config.llm_key}',
                }, json=corpo, timeout=self.config.timeout)
                r.raise_for_status()
                conteudo = r.json()['choices'][0]['message']['content']
            return esquema.model_validate(json.loads(conteudo)).model_dump()
        except httpx.HTTPStatusError as erro:
            if self.config.provider == 'openrouter':
                mensagens_erro = {
                    429: 'O limite de uso gratuito do OpenRouter foi atingido ou o provedor está sobrecarregado. Aguarde antes de tentar novamente; a conversa foi preservada.',
                    401: 'A chave do OpenRouter é inválida. Confira OPEN_ROUTER_KEY no backend/.env; a conversa foi preservada.',
                    403: 'A chave ou a conta do OpenRouter não tem acesso a este modelo. Verifique a configuração; a conversa foi preservada.',
                    402: 'O OpenRouter recusou a requisição por uma restrição da conta. Verifique a conta mantendo um modelo gratuito; a conversa foi preservada.',
                }
                if erro.response.status_code in mensagens_erro:
                    raise ModeloIndisponivel(mensagens_erro[erro.response.status_code]) from erro
            raise ModeloIndisponivel('O modelo está indisponível. Tente novamente; a conversa foi preservada.') from erro
        except (httpx.HTTPError, ValueError, KeyError, IndexError, TypeError) as erro:
            raise ModeloIndisponivel('O modelo está indisponível ou retornou uma resposta inválida. Tente novamente; a conversa foi preservada.') from erro
