import os
from pathlib import Path
import requests
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parents[1] / '.env')


class ErroAPI(Exception):
    pass


class APIClient:
    def __init__(self):
        self.url = os.getenv('API_URL', 'http://localhost:8000').rstrip('/')
        self.chave = os.getenv('API_KEY', '')
        self.timeout = float(os.getenv('API_TIMEOUT', '75'))

    def consultar(self, caminho):
        try:
            resposta = requests.get(self.url + caminho,
                                   headers={'X-API-Key': self.chave}, timeout=self.timeout)
            if resposta.status_code == 401:
                raise ErroAPI('Chave inválida. Confira API_KEY no painel e no backend.')
            if not resposta.ok:
                raise ErroAPI('A API não conseguiu consultar o atendimento. Atualize a fila.')
            return resposta.json()
        except (requests.RequestException, ValueError):
            raise ErroAPI('Não foi possível consultar a API. Verifique o backend e API_URL.')

    def handoffs(self):
        return self.consultar('/handoffs')

    def sessao(self, sid):
        return self.consultar(f'/sessions/{sid}')
