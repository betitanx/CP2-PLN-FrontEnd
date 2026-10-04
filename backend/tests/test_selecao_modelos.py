import json
import httpx
from app.llm.client import LLMClient
from app.llm.models import MODELOS_GRATUITOS
from app.memory.store import Store
from test_contrato import cliente, sessao, falar


def test_troca_preserva_estado_isola_sessoes_e_envia_modelo(cliente, monkeypatch):
    bot = cliente.app.state.bot
    bot.config.provider = 'openrouter'
    bot.config.model = next(iter(MODELOS_GRATUITOS))
    bot.config.llm_key = 'chave-ficticia'
    bot.config.url = 'https://openrouter.ai/api/v1'
    bot.llm = LLMClient(bot.config)
    ids = list(MODELOS_GRATUITOS)
    assert [m['id'] for m in cliente.get('/models').json()] == ids
    a, b = sessao(cliente), sessao(cliente)
    falar(cliente, a, 'Qual o endereço?')
    antes = cliente.get(f'/sessions/{a}').json()
    chamadas = []
    def responder(url, **kwargs):
        chamadas.append(kwargs['json'])
        return httpx.Response(200, json={'choices': [{'message': {'content':
            json.dumps({'intent': 'desconhecida'})}}]}, request=httpx.Request('POST', url))
    monkeypatch.setattr(httpx, 'post', responder)
    for modelo in reversed(ids):
        r = cliente.patch(f'/sessions/{a}/model', json={'model': modelo})
        assert r.status_code == 200
        assert r.json()['history'][:len(antes['history'])] == antes['history']
        assert r.json()['slots'] == antes['slots']
        assert Store(bot.config.database).obter(a)['model'] == modelo
        falar(cliente, a, 'Gostaria de verificar uma possibilidade diferente')
        assert chamadas[-1]['model'] == modelo
        assert chamadas[-1]['provider']['max_price']['completion'] == 0
        assert chamadas[-1]['reasoning'] == {'enabled': False}
    assert cliente.get(f'/sessions/{b}').json()['model'] == ids[0]
    assert cliente.get(f'/sessions/{b}').json()['turn'] == 0


def test_seletor_recusa_modelos_nao_permitidos_e_exige_autenticacao(cliente):
    sid = sessao(cliente)
    caminho = f'/sessions/{sid}/model'
    assert cliente.patch(caminho, json={'model': 'modelo/pago'}).status_code == 422
    assert cliente.patch(caminho, json={}).status_code == 422
    assert cliente.get('/models', headers={'X-API-Key': 'errada'}).status_code == 401
    modelo = cliente.app.state.bot.config.model
    assert cliente.patch('/sessions/ausente/model', json={'model': modelo}).status_code == 404
    assert cliente.patch(caminho, json={'model': modelo},
                         headers={'X-API-Key': 'errada'}).status_code == 401
