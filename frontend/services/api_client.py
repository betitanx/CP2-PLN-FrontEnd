import os
from pathlib import Path
import requests
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parents[1] / '.env')


class ErroAPI(Exception):
    def __init__(self, mensagem, status=None):
        super().__init__(mensagem)
        self.status = status


class APIClient:
    def __init__(self):
        self.url = os.getenv('API_URL', 'http://localhost:8000').rstrip('/')
        self.key = os.getenv('API_KEY', '')
        self.timeout = float(os.getenv('API_TIMEOUT', '75'))

    def requisitar(self, metodo, caminho, dados=None):
        try:
            r = requests.request(metodo, self.url+caminho, json=dados,
                                 headers={'X-API-Key':self.key}, timeout=self.timeout)
        except requests.Timeout:
            raise ErroAPI('A resposta demorou mais que o esperado. Atualize a conversa para conferir se a mensagem foi processada antes de reenviar.')
        except requests.RequestException:
            raise ErroAPI('Não foi possível conectar à API. Verifique se o backend está em execução e se API_URL está correta.')
        if not r.ok:
            mensagens = {401:'Chave de acesso inválida. Confira API_KEY nos dois projetos.',
                        404:'Conversa não encontrada. Inicie uma nova conversa.',
                        422:'Mensagem ou avaliação inválida. Confira os dados enviados.',
                        503:'O modelo está indisponível. Sua conversa foi preservada; tente novamente.'}
            mensagem = mensagens.get(r.status_code, 'A API não conseguiu concluir a operação. Tente novamente.')
            if r.status_code == 503:
                try:
                    detalhe = r.json().get('detail')
                    if isinstance(detalhe, str) and detalhe:
                        mensagem = detalhe[:400]
                except (ValueError, AttributeError):
                    pass
            raise ErroAPI(mensagem, r.status_code)
        if r.status_code == 204:
            return None
        try:
            return r.json()
        except ValueError:
            raise ErroAPI('A API retornou uma resposta inválida. Verifique a configuração.')

    def criar_sessao(self):
        return self.requisitar('POST','/sessions')

    def sessao(self, sid):
        return self.requisitar('GET',f'/sessions/{sid}')

    def chat(self, sid, mensagem):
        return self.requisitar('POST','/chat',{'session_id':sid,'message':mensagem})

    def modelos(self):
        return self.requisitar('GET', '/models')

    def selecionar_modelo(self, sid, modelo):
        return self.requisitar('PATCH', f'/sessions/{sid}/model', {'model': modelo})

    def metrics(self):
        return self.requisitar('GET','/metrics')

    def health(self):
        return self.requisitar('GET','/health')

    def apagar(self, sid):
        return self.requisitar('DELETE',f'/sessions/{sid}')

    def feedback(self, sid, nota):
        return self.requisitar('POST','/feedback',{'session_id':sid,'rating':nota})

    def handoffs(self):
        return self.requisitar('GET','/handoffs')

    def avaliar(self, sid):
        return self.requisitar('POST', f'/sessions/{sid}/avaliacao')

    def avaliacao(self, sid):
        return self.requisitar('GET', f'/sessions/{sid}/avaliacao')
