from test_contrato import cliente, sessao, falar


def test_duas_validacoes_invalidas_oferecem_humano(cliente):
    sid = sessao(cliente)
    falar(cliente, sid, 'agendar')
    falar(cliente, sid, 'Marina Alves')
    falar(cliente, sid, 'XYZ')
    r = falar(cliente, sid, '123')
    assert r['fallback']
    assert 'humano' in r['reply']
    assert r['slots']['nome'] == 'Marina Alves'
    assert falar(cliente, sid, 'sim')['handoff']['active']


def test_handoff_preserva_relato_original_apos_complemento(cliente):
    sid = sessao(cliente)
    falar(cliente, sid, 'Estou frustrada e quero reclamar')
    r = falar(cliente, sid, 'Também quero registrar a placa ABC1D23')
    resumo = r['handoff']['summary']['relato']
    assert 'frustrada' in resumo
    assert 'ABC1D23' in resumo


def test_conteudo_nulo_do_modelo_retorna_503(cliente, monkeypatch):
    import httpx
    from app.llm.client import LLMClient
    cliente.app.state.bot.llm = LLMClient(cliente.app.state.bot.config)
    def responder(url, **kwargs):
        return httpx.Response(200, json={'message':{'content':None}}, request=httpx.Request('POST',url))
    monkeypatch.setattr(httpx, 'post', responder)
    sid = sessao(cliente)
    r = cliente.post('/chat', json={'session_id':sid,'message':'Uma solicitação diferente'})
    assert r.status_code == 503
    assert cliente.get(f'/sessions/{sid}').json()['turn'] == 0
