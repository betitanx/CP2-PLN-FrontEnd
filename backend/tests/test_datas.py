import pytest
from test_contrato import cliente, sessao, falar


def preparar(cliente):
    sid = sessao(cliente)
    for mensagem in ['agendar', 'Marina Teste', 'ABC1D23']:
        resposta = falar(cliente, sid, mensagem)
    assert 'DD/MM/AAAA' in resposta['reply']
    return sid


def test_data_brasileira_na_memoria_e_confirmacao(cliente):
    sid = preparar(cliente)
    falar(cliente, sid, '06/10/2026')
    resposta = falar(cliente, sid, 'E aqueles horários que você sugeriu?')
    assert '06/10/2026' in resposta['reply']
    assert resposta['slots']['data'] == '2026-10-06'
    resposta = falar(cliente, sid, '09:00')
    assert '06/10/2026' in resposta['reply']
    resposta = falar(cliente, sid, 'confirmar')
    assert resposta['status'] == 'encerrada'
    assert '06/10/2026' in resposta['reply']


@pytest.mark.parametrize('entrada', ['31/02/2026', '00/10/2026', '10/13/2026', '6/10/2026', '2026-02-31'])
def test_data_invalida_preserva_slots(cliente, entrada):
    sid = preparar(cliente)
    resposta = falar(cliente, sid, entrada)
    assert resposta['fallback']
    assert 'DD/MM/AAAA' in resposta['reply']
    assert resposta['slots'] == {'nome': 'Marina Teste', 'placa': 'ABC1D23', 'data': None, 'horario': None}


def test_iso_e_brasileiro_usam_a_mesma_reserva(cliente):
    sid = preparar(cliente)
    for mensagem in ['06/10/2026', '09:00', 'confirmar']:
        falar(cliente, sid, mensagem)
    outro = preparar(cliente)
    resposta = falar(cliente, outro, '2026-10-06')
    assert resposta['slots']['data'] == '2026-10-06'
    assert '09:00' not in resposta['reply']
    assert '11:00' in resposta['reply']


def test_feriado_brasileiro_consulta_agenda_iso(cliente):
    sid = preparar(cliente)
    resposta = falar(cliente, sid, '12/10/2026')
    assert resposta['fallback'] and 'fechada' in resposta['reply']
    assert resposta['slots']['data'] is None
