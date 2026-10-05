from pathlib import Path
import json
import requests
from streamlit.testing.v1 import AppTest


def test_painel_consulta_handoff_e_historico_pela_api(monkeypatch):
    chamadas = []
    def responder(url, **kwargs):
        chamadas.append(url)
        dados = [{'session_id': 'sessao-ficticia', 'handoff': {
            'reason': 'frustração', 'summary': {'intencao': 'humano',
            'dados': {'nome': 'Marina Teste', 'data': '2026-10-06'},
            'relato': 'Quero reclamar', 'acoes': ['Transferência registrada']}}}]
        if '/sessions/' in url:
            dados = {'history': [{'role': 'user', 'content': 'Quero reclamar'}]}
        r = requests.Response()
        r.status_code = 200
        r._content = json.dumps(dados).encode()
        return r
    monkeypatch.setattr(requests, 'get', responder)
    app = AppTest.from_file(str(Path(__file__).resolve().parents[1] / 'app.py')).run()
    assert not app.exception
    assert app.metric[0].value == '1'
    assert '06/10/2026' in app.json[0].value
    app.checkbox[0].check().run()
    assert not app.exception
    assert any(url.endswith('/handoffs') for url in chamadas)
    assert any(url.endswith('/sessions/sessao-ficticia') for url in chamadas)


def test_painel_sem_backend_nao_mostra_traceback(monkeypatch):
    def falhar(*args, **kwargs):
        raise requests.ConnectionError()
    monkeypatch.setattr(requests, 'get', falhar)
    app = AppTest.from_file(str(Path(__file__).resolve().parents[1] / 'app.py')).run()
    assert not app.exception
    assert 'Não foi possível consultar' in app.error[0].value
