import pytest
import requests
from services.api_client import APIClient, ErroAPI


@pytest.mark.parametrize('status', [401,404,422,503])
def test_erros_http_sao_mensagens_amigaveis(monkeypatch, status):
    def responder(*args, **kwargs):
        r = requests.Response()
        r.status_code = status
        return r
    monkeypatch.setattr(requests, 'request', responder)
    with pytest.raises(ErroAPI) as erro:
        APIClient().sessao('ficticia')
    assert erro.value.status == status
    assert 'Traceback' not in str(erro.value)


def test_frontend_sem_api_mostra_erro_sem_traceback(monkeypatch):
    from pathlib import Path
    from streamlit.testing.v1 import AppTest
    def falhar(*args, **kwargs):
        raise requests.ConnectionError('Falha interna que não deve aparecer na tela')
    monkeypatch.setattr(requests, 'request', falhar)
    app = AppTest.from_file(str(Path(__file__).resolve().parents[1] / 'app.py')).run()
    assert not app.exception
    assert 'Não foi possível conectar à API' in app.error[0].value


def test_timeout_orienta_atualizar_antes_de_reenviar(monkeypatch):
    def falhar(*args, **kwargs):
        raise requests.Timeout()
    monkeypatch.setattr(requests, 'request', falhar)
    with pytest.raises(ErroAPI, match='antes de reenviar'):
        APIClient().chat('ficticia','oi')


def test_limite_gratuito_e_exibido_na_tela(monkeypatch):
    def responder(*args, **kwargs):
        r = requests.Response()
        r.status_code = 503
        r._content = '{"detail":"O limite de uso gratuito do OpenRouter foi atingido. Aguarde."}'.encode('utf-8')
        return r
    monkeypatch.setattr(requests, 'request', responder)
    with pytest.raises(ErroAPI, match='limite de uso gratuito'):
        APIClient().chat('ficticia', 'oi')


def test_seletor_aplica_modelo_por_http_e_preserva_identificador(monkeypatch):
    import json
    from pathlib import Path
    from streamlit.testing.v1 import AppTest
    ids = ['google/gemma-4-26b-a4b-it:free', 'nvidia/nemotron-3-super-120b-a12b:free']
    sessao = {'session_id': 'ficticia', 'model': ids[0], 'history': [],
              'slots': {}, 'last_turn': None, 'status': 'ativa', 'turn': 0,
              'handoff': {'active': False}}
    chamadas = []
    def responder(metodo, url, **kwargs):
        chamadas.append((metodo, url, kwargs.get('json')))
        if metodo == 'PATCH':
            sessao['model'] = kwargs['json']['model']
        dados = ([{'id': ids[0], 'name': 'Gemma'}, {'id': ids[1], 'name': 'Nemotron'}]
                 if url.endswith('/models') else sessao)
        r = requests.Response()
        r.status_code = 200
        r._content = json.dumps(dados).encode()
        return r
    monkeypatch.setattr(requests, 'request', responder)
    app = AppTest.from_file(str(Path(__file__).resolve().parents[1] / 'app.py')).run()
    assert not app.exception
    app.selectbox[0].select(ids[1])
    next(b for b in app.button if b.label == 'Aplicar modelo').click().run()
    assert not app.exception
    assert any(m == 'PATCH' and u.endswith('/sessions/ficticia/model')
               and d == {'model': ids[1]} for m, u, d in chamadas)
    assert app.session_state['session_id'] == 'ficticia'
    assert app.selectbox[0].value == ids[1]
