import streamlit as st


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
    st.json(sessao['slots'])
    if sessao['handoff']['active']:
        st.warning('Atendimento humano solicitado')
        st.json(sessao['handoff'])


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
    if dados['fallback_por_intencao']:
        st.bar_chart(dados['fallback_por_intencao'])
    with st.expander('Dados da API'):
        st.json(dados)
