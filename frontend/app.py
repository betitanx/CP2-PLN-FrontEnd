import streamlit as st
from services.api_client import APIClient, ErroAPI
from components.panels import raio_x, metricas, slots_para_exibir, avaliacao_llm

st.set_page_config(page_title='Prosa | Roda Certa', page_icon='💬', layout='wide')
api = APIClient()
st.title('Oficina Roda Certa')

try:
    with st.sidebar:
        st.header('Prosa')
        pagina = st.radio('Área', ['Conversa', 'Métricas', 'Atendimento humano'])
        if st.button('Nova conversa', use_container_width=True):
            st.session_state['session_id'] = api.criar_sessao()['session_id']
            st.rerun()
        if 'session_id' in st.session_state:
            st.write('**Sessão**')
            st.code(st.session_state['session_id'], language=None)
        st.button('Atualizar', use_container_width=True)

    if pagina == 'Métricas':
        metricas(api.metrics())
    elif pagina == 'Atendimento humano':
        st.subheader('Fila de atendimento')
        fila = api.handoffs()
        if not fila:
            st.info('Nenhuma conversa aguardando atendimento.')
        for item in fila:
            with st.expander(item['session_id']):
                resumo = item['handoff']
                resumo['summary']['dados'] = slots_para_exibir(resumo['summary']['dados'])
                st.json(resumo)
    else:
        if 'session_id' not in st.session_state:
            st.session_state['session_id'] = api.criar_sessao()['session_id']
            st.rerun()
        # Apenas o identificador da conversa é persistido pela aplicação na tela.
        # Histórico, slots e último turno são obtidos por HTTP a cada execução.
        sessao = api.sessao(st.session_state['session_id'])
        with st.sidebar:
            modelos = {item['id']: item['name'] for item in api.modelos()}
            atual = sessao.get('model')
            ids = list(modelos)
            # O seletor é reconstruído do estado persistido pela API.
            with st.form('modelo_da_conversa'):
                escolhido = st.selectbox('Modelo', ids, format_func=modelos.get,
                                        index=ids.index(atual) if atual in ids else 0)
                if st.form_submit_button('Aplicar modelo'):
                    api.selecionar_modelo(sessao['session_id'], escolhido)
                    st.rerun()
        chat, painel = st.columns([2, 1], gap='large')
        with painel:
            raio_x(sessao)
            with st.expander('Avaliação por LLM'):
                julgamento = api.avaliacao(sessao['session_id'])
                if st.button('Avaliar qualidade', disabled=sessao['turn'] == 0):
                    with st.spinner('Avaliando conversa…'):
                        julgamento = api.avaliar(sessao['session_id'])
                if julgamento:
                    avaliacao_llm(julgamento, sessao['turn'])
            with st.form('avaliacao'):
                nota = st.select_slider('Avaliação', options=[1,2,3,4,5], value=5)
                if st.form_submit_button('Enviar avaliação'):
                    api.feedback(sessao['session_id'], nota)
                    st.success('Avaliação registrada.')
            with st.expander('Apagar conversa'):
                st.write('Apaga histórico, avaliação e reserva fictícia desta sessão.')
                if st.button('Apagar permanentemente'):
                    api.apagar(sessao['session_id'])
                    del st.session_state['session_id']
                    st.rerun()
        with chat:
            for msg in sessao['history']:
                with st.chat_message(msg['role']):
                    st.write(msg['content'])
            mensagem = st.chat_input('Escreva sua mensagem', max_chars=2000)
            if mensagem:
                with st.spinner('Lia está respondendo…'):
                    api.chat(sessao['session_id'], mensagem)
                st.rerun()
except ErroAPI as erro:
    st.error(str(erro))
    if erro.status == 404:
        st.session_state.pop('session_id', None)
    if st.button('Tentar novamente'):
        st.rerun()
