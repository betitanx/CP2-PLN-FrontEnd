import re
import unicodedata


def normalizar(texto):
    return ''.join(c for c in unicodedata.normalize('NFD', texto.lower()) if unicodedata.category(c) != 'Mn')


def detectar_intencao(texto):
    t = normalizar(texto)
    regras = [
        ('humano', r'\b(humano|atendente|reclamar|reclamacao|gerente)\b'),
        ('memoria', r'(aquele|aqueles|sugeriu|meu nome|minha placa|qual.*marcado)'),
        ('agendar', r'\b(agendar|agendamento|marcar|reservar)\b'),
        ('encerrar', r'\b(encerrar|finalizar|tchau)\b'),
        ('cancelar', r'\b(cancelar|desistir)\b'),
        ('saudacao', r'^(oi|ola|bom dia|boa tarde|boa noite)[!. ]*$'),
        ('agradecer', r'^(obrigad[oa]|valeu)[!. ]*$'),
    ]
    return next((i for i, p in regras if re.search(p, t)), 'desconhecida')
