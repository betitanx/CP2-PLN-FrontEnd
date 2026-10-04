import re
from .nlu import normalizar


def verificar_entrada(texto):
    t = normalizar(texto)
    if re.search(r'(ignore|esqueca|desconsidere).*(instruc|regras|prompt)|mostre.*(prompt|instruc)|system prompt|finja ser|<\|.*\|>|\[inst\]', t):
        return 'injecao'
    if re.search(r'\b(hackear|explosivo|arma|politica|eleicao)\b', t):
        return 'fora_escopo'
    return None


def situacao_sensivel(texto):
    return bool(re.search(r'\b(acidente|ferid[oa]|incendio|ameaca|urgente|urgencia|freio.*falh|vazamento.*combustivel)\b', normalizar(texto)))


def verificar_saida(texto, llm=False):
    eventos = []
    if llm and (re.search(r'\d|confirmad|garant|promet|desconto|gratis|gratuit|prompt|system|instruc', normalizar(texto)) or texto.count('?') > 1):
        eventos.append('saida:promessa_ou_conteudo_nao_autorizado')
        texto = 'Posso ajudar com agendamento, informações da oficina ou atendimento humano. Qual opção deseja?'
    if len(texto) > 600:
        eventos.append('saida:tamanho')
        texto = texto[:597].rsplit(' ', 1)[0] + '…'
    return texto, eventos
