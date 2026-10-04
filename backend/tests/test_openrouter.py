import json
import httpx
import pytest
from app.config import Config
from app.llm.client import LLMClient
from test_contrato import cliente, sessao


def configurar(monkeypatch):
    monkeypatch.setenv('API_KEY', 'chave-local-de-teste')
    monkeypatch.setenv('LLM_PROVIDER', 'openrouter')
    monkeypatch.setenv('LLM_MODEL', 'openrouter/free')
    monkeypatch.setenv('LLM_URL', 'https://openrouter.ai/api/v1')
    monkeypatch.setenv('OPEN_ROUTER_KEY', 'chave-ficticia-do-provedor')
    monkeypatch.setenv('LLM_API_KEY', 'nao-usar-no-openrouter')


def test_openrouter_configura_modelo_gratuito(monkeypatch):
    configurar(monkeypatch)
    config = Config()
    assert config.provider == 'openrouter'
    assert config.model == 'openrouter/free'
    assert config.llm_key == 'chave-ficticia-do-provedor'


def test_openrouter_nao_usa_variavel_antiga(monkeypatch):
    configurar(monkeypatch)
    monkeypatch.setenv('OPEN_ROUTER_KEY', '')
    assert Config().llm_key == ''


def test_openrouter_recusa_modelo_pago(monkeypatch):
    configurar(monkeypatch)
    monkeypatch.setenv('LLM_MODEL', 'modelo/pago')
    with pytest.raises(RuntimeError, match='gratuito'):
        Config()


def test_openrouter_envia_json_e_restringe_preco(monkeypatch):
    configurar(monkeypatch)
    chamadas = []
    def responder(url, **kwargs):
        chamadas.append((url, kwargs))
        resposta = json.dumps({'intent':'agendar','faq_id':None,'reply':''})
        return httpx.Response(200, json={'choices':[{'message':{'content':resposta}}]}, request=httpx.Request('POST',url))
    monkeypatch.setattr(httpx, 'post', responder)
    llm = LLMClient(Config())
    assert llm.analisar([{'role':'user','content':'Quero uma visita'}])['intent'] == 'agendar'
    url, envio = chamadas[0]
    assert url == 'https://openrouter.ai/api/v1/chat/completions'
    assert envio['headers']['Authorization'] == 'Bearer chave-ficticia-do-provedor'
    assert envio['json']['response_format'] == {'type':'json_object'}
    assert envio['json']['provider']['require_parameters'] is True
    assert envio['json']['provider']['max_price'] == {'prompt':0,'completion':0,'request':0}
    assert 'models' not in envio['json'] and 'plugins' not in envio['json']


@pytest.mark.parametrize('codigo,trecho', [(429,'limite'),(401,'chave'),(402,'conta')])
def test_falha_do_openrouter_preserva_sessao(cliente, monkeypatch, codigo, trecho):
    configurar(monkeypatch)
    monkeypatch.setenv('API_KEY', 'chave-de-teste')
    cliente.app.state.bot.config = Config()
    cliente.app.state.bot.llm = LLMClient(cliente.app.state.bot.config)
    def falhar(url, **kwargs):
        return httpx.Response(codigo, json={'error':{'message':'Detalhe interno do provedor'}}, request=httpx.Request('POST',url))
    monkeypatch.setattr(httpx, 'post', falhar)
    sid = sessao(cliente)
    r = cliente.post('/chat', json={'session_id':sid,'message':'Me ajude com algo diferente'})
    assert r.status_code == 503
    assert trecho in r.json()['detail'].lower()
    assert cliente.get(f'/sessions/{sid}').json()['turn'] == 0
    assert cliente.get('/metrics').json()['erros_modelo'] == 1
