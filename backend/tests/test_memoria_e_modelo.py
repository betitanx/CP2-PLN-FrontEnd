import json
import pytest
from app.llm.client import LLMClient, ModeloIndisponivel
from app.nlp.guardrails import verificar_saida
from test_contrato import cliente, sessao, falar


def test_janela_envia_contexto_real_do_servidor(cliente):
    sid = sessao(cliente)
    for mensagem in ['agendar','Marina Alves','ABC1D23','2026-10-06','Qual o endereço?']:
        falar(cliente, sid, mensagem)
    bot = cliente.app.state.bot
    bot.config.turns = 2
    mensagens = bot.mensagens(bot.store.obter(sid), 'retomar')
    assert len(mensagens) == 7  # 2 system, 4 falas antigas, 1 nova
    assert 'Marina Alves' in mensagens[1]['content']
    assert mensagens[-1]['content'] == 'retomar'
    assert mensagens[-2]['role'] == 'assistant'


def test_saida_bloqueia_promessas_e_limita_tamanho():
    texto, eventos = verificar_saida('Garanto reparo grátis amanhã.', llm=True)
    assert 'garanto' not in texto.lower()
    assert eventos
    texto, eventos = verificar_saida('Palavra ' * 200)
    assert len(texto) <= 600
    assert eventos == ['saida:tamanho']


def test_sessoes_isoladas_e_persistentes(cliente):
    from app.memory.store import Store
    a, b = sessao(cliente), sessao(cliente)
    falar(cliente, a, 'agendar')
    falar(cliente, a, 'Marina Alves')
    assert cliente.get(f'/sessions/{b}').json()['slots']['nome'] is None
    nova_instancia = Store(cliente.app.state.bot.config.database)
    assert nova_instancia.obter(a)['slots']['nome'] == 'Marina Alves'


def test_metricas_nao_confundem_ativa_com_contida(cliente):
    sid = sessao(cliente)
    falar(cliente, sid, 'Qual o endereço?')
    assert cliente.get('/metrics').json()['taxa_contencao'] == 0
    falar(cliente, sid, 'encerrar')
    assert cliente.get('/metrics').json()['taxa_contencao'] == 1


@pytest.mark.parametrize('provider', ['ollama', 'openai_compatible'])
def test_contrato_do_provedor_e_json_invalido(cliente, monkeypatch, provider):
    import httpx
    bot = cliente.app.state.bot
    bot.config.provider = provider
    chamadas = []
    def responder(url, **kwargs):
        chamadas.append((url, kwargs))
        corpo = json.dumps({'intent':'agendar','faq_id':None,'reply':''})
        payload = {'message':{'content':corpo}} if provider == 'ollama' else {'choices':[{'message':{'content':corpo}}]}
        return httpx.Response(200, json=payload, request=httpx.Request('POST', url))
    monkeypatch.setattr(httpx, 'post', responder)
    real = LLMClient(bot.config)
    mensagens = [{'role':'system','content':'Português'},{'role':'user','content':'Quero uma visita'}]
    assert real.analisar(mensagens)['intent'] == 'agendar'
    assert chamadas[0][1]['json']['messages'] == mensagens
    def invalida(url, **kwargs):
        payload = {'message':{'content':'{}'}} if provider == 'ollama' else {'choices':[{'message':{'content':'{}'}}]}
        return httpx.Response(200, json=payload, request=httpx.Request('POST',url))
    monkeypatch.setattr(httpx, 'post', invalida)
    with pytest.raises(ModeloIndisponivel):
        real.analisar(mensagens)
