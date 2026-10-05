from datetime import date
import streamlit as st
from services.api_client import APIClient, ErroAPI

st.set_page_config(page_title='Prosa | Atendente', page_icon='📋', layout='wide')
st.title('Painel do atendente')
st.button('Atualizar fila')
api = APIClient()

try:
    fila = api.handoffs()
    st.metric('Atendimentos aguardando', len(fila))
    if not fila:
        st.info('Nenhum atendimento aguardando.')
    for item in fila:
        handoff = item['handoff']
        resumo = handoff['summary']
        with st.expander(f"{resumo['dados'].get('nome') or 'Pessoa não identificada'} · {item['session_id']}"):
            st.write('**Motivo:**', handoff['reason'])
            st.write('**Intenção:**', resumo['intencao'])
            dados = dict(resumo['dados'])
            if dados.get('data'):
                dados['data'] = date.fromisoformat(dados['data']).strftime('%d/%m/%Y')
            st.write('**Dados coletados**')
            st.json(dados)
            st.write('**Relato:**', resumo['relato'])
            st.write('**Ações realizadas**')
            for acao in resumo['acoes']:
                st.write('• ' + acao)
            if st.checkbox('Mostrar histórico', key=item['session_id']):
                for mensagem in api.sessao(item['session_id'])['history']:
                    with st.chat_message(mensagem['role']):
                        st.write(mensagem['content'])
except ErroAPI as erro:
    st.error(str(erro))
