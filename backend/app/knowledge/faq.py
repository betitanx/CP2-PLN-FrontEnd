import json
from app.config import BASE
from app.nlp.nlu import normalizar

FAQ = json.loads((BASE / 'data/faq.json').read_text(encoding='utf-8'))


def buscar_faq(pergunta):
    texto = normalizar(pergunta)
    return next((item for item in FAQ if any(g in texto for g in item['gatilhos'])), None)
