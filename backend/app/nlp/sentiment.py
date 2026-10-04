import re
from .nlu import normalizar


def analisar_sentimento(texto):
    t = normalizar(texto)
    negativo = bool(re.search(r'\b(frustrad[oa]|irritad[oa]|raiva|pessim[oa]|absurdo|reclamar|reclamacao|horrivel|insatisfeit[oa])\b', t))
    positivo = bool(re.search(r'\b(otimo|excelente|obrigad[oa]|adorei|perfeito)\b', t))
    return {'label': 'negativo' if negativo else 'positivo' if positivo else 'neutro', 'score': 0.9 if negativo or positivo else 0.6}
