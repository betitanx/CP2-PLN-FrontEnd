from copy import deepcopy
from datetime import date
import streamlit as st


def slots_para_exibir(slots):
    exibidos = dict(slots)
    if exibidos.get('data'):
        exibidos['data'] = date.fromisoformat(exibidos['data']).strftime('%d/%m/%Y')
    return exibidos


def raio_x(sessao):
    st.subheader('Raio-X do turno')
    turno = sessao['last_turn']
    if turno:
        st.write('**Intenção:**', turno['intent'])
        st.write('**Sentimento:**', turno['sentiment']['label'])
        st.write('**Fallback:**', 'Sim' if turno['fallback'] else 'Não')
        st.write('**Latência:**', f"{turno['latency_ms']:.0f} ms")
        st.write('**Turno:**', turno['turn'])
    st.write('**Situação:**', sessao['status'])
    st.write('**Slots**')
    st.json(slots_para_exibir(sessao['slots']))
    if sessao['handoff']['active']:
        st.warning('Atendimento humano solicitado')
        resumo = deepcopy(sessao['handoff'])
        resumo['summary']['dados'] = slots_para_exibir(resumo['summary']['dados'])
        st.json(resumo)


def metricas(dados):
    st.subheader('Métricas de atendimento')
    a, b, c, d = st.columns(4)
    a.metric('Contenção', f"{dados['taxa_contencao']:.1%}")
    b.metric('Fallback', f"{dados['taxa_fallback']:.1%}")
    c.metric('Handoff', f"{dados['taxa_handoff']:.1%}")
    d.metric('Mensagens por conversa', f"{dados['mensagens_por_conversa']:.1f}")
    a, b, c = st.columns(3)
    a.metric('Conversas', dados['total_conversas'])
    b.metric('Latência média', f"{dados['latencia_media_ms']:.0f} ms")
    c.metric('CSAT', f"{dados['csat_medio']:.1f}/5" if dados['csat_medio'] is not None else 'Sem avaliações')
    st.subheader('CSAT por resultado da conversa')
    nomes = {'contida': 'Encerrada sem handoff', 'handoff': 'Transferida para humano',
             'em_andamento': 'Em andamento'}
    st.dataframe([{'Resultado': nomes[k], 'Conversas': v['conversas'],
                   'Avaliações': v['avaliacoes'],
                   'CSAT': f"{v['media']:.1f}/5" if v['media'] is not None else 'Sem avaliações'}
                  for k, v in dados['csat_por_resultado'].items()], hide_index=True,
                 use_container_width=True)
    if dados['fallback_por_intencao']:
        st.bar_chart(dados['fallback_por_intencao'])
    with st.expander('Dados da API'):
        st.json(dados)


def avaliacao_llm(dados, turno):
    st.caption('Avaliação automática; requer revisão humana e não equivale ao CSAT.')
    st.write('**Modelo:**', dados['modelo'])
    st.write('**Turnos avaliados:**', dados['turnos_avaliados'])
    if dados['turnos_avaliados'] != turno:
        st.warning('A conversa mudou após esta avaliação. Avalie novamente para incluir os novos turnos.')
    nomes = {'relevancia': 'Relevância', 'aderencia_persona': 'Aderência à persona',
             'retencao_contexto': 'Retenção de contexto'}
    for criterio, valor in dados['resultado'].items():
        st.write(f"**{nomes[criterio]}: {valor['nota']}/5**")
        st.write(valor['justificativa'])
