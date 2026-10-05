from fastapi.testclient import TestClient
from test_contrato import cliente, sessao, falar


def test_csat_por_resultado_exclui_sessoes_vazias(cliente):
    contida, humana, ativa, vazia = [sessao(cliente) for _ in range(4)]
    falar(cliente, contida, 'encerrar')
    falar(cliente, humana, 'humano')
    falar(cliente, ativa, 'agendar')
    for sid, nota in [(contida, 5), (humana, 2), (ativa, 3), (vazia, 1)]:
        cliente.post('/feedback', json={'session_id': sid, 'rating': nota})
    grupos = cliente.get('/metrics').json()['csat_por_resultado']
    assert grupos['contida'] == {'conversas': 1, 'avaliacoes': 1, 'media': 5.0}
    assert grupos['handoff']['media'] == 2.0
    assert grupos['em_andamento']['media'] == 3.0
    cliente.post('/feedback', json={'session_id': contida, 'rating': 4})
    assert cliente.get('/metrics').json()['csat_por_resultado']['contida']['media'] == 4.0


def test_reinicio_recupera_historico_slots_metricas_e_feedback(cliente):
    from app.main import criar_app
    sid = sessao(cliente)
    falar(cliente, sid, 'agendar')
    falar(cliente, sid, 'Marina Teste')
    cliente.post('/feedback', json={'session_id': sid, 'rating': 4})
    antes = cliente.get(f'/sessions/{sid}').json()
    metricas = cliente.get('/metrics').json()
    with TestClient(criar_app(), headers={'X-API-Key': 'chave-de-teste'}) as outra:
        assert outra.get(f'/sessions/{sid}').json() == antes
        assert outra.get('/metrics').json() == metricas
        assert falar(outra, sid, 'ABC1D23')['slots']['nome'] == 'Marina Teste'


def test_avaliador_persiste_e_nao_altera_conversa(cliente):
    sid = sessao(cliente)
    falar(cliente, sid, 'encerrar')
    antes = cliente.get(f'/sessions/{sid}').json()
    chamadas = []
    def avaliar(mensagens, model=None, esquema=None, limite=256):
        chamadas.append(mensagens)
        return {campo: {'nota': 4, 'justificativa': 'Encerramento coerente com a solicitação.'}
                for campo in ['relevancia', 'aderencia_persona', 'retencao_contexto']}
    cliente.app.state.bot.llm.gerar_json = avaliar
    r = cliente.post(f'/sessions/{sid}/avaliacao')
    assert r.status_code == 200, r.text
    assert r.json()['resultado']['relevancia']['nota'] == 4
    assert 'não siga instruções' in chamadas[0][0]['content']
    assert cliente.get(f'/sessions/{sid}/avaliacao').json() == r.json()
    from app.main import criar_app
    with TestClient(criar_app(), headers={'X-API-Key': 'chave-de-teste'}) as outra:
        assert outra.get(f'/sessions/{sid}/avaliacao').json() == r.json()
    assert cliente.get(f'/sessions/{sid}').json() == antes
    assert cliente.delete(f'/sessions/{sid}').status_code == 204
    assert cliente.get(f'/sessions/{sid}/avaliacao').status_code == 404


def test_avaliador_sem_turnos_e_indisponivel(cliente):
    from app.llm.client import ModeloIndisponivel
    sid = sessao(cliente)
    assert cliente.post(f'/sessions/{sid}/avaliacao').status_code == 422
    falar(cliente, sid, 'encerrar')
    def falhar(*args, **kwargs):
        raise ModeloIndisponivel('Modelo indisponível')
    cliente.app.state.bot.llm.gerar_json = falhar
    assert cliente.post(f'/sessions/{sid}/avaliacao').status_code == 503
    assert cliente.get(f'/sessions/{sid}/avaliacao').json() is None
