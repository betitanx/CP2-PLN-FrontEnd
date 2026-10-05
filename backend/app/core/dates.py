"""Datas brasileiras na conversa, ISO para agenda e persistência."""
import re
from datetime import date, datetime


def interpretar_data(texto):
    if re.fullmatch(r'\d{2}/\d{2}/\d{4}', texto):
        return datetime.strptime(texto, '%d/%m/%Y').date()
    if re.fullmatch(r'\d{4}-\d{2}-\d{2}', texto):
        return date.fromisoformat(texto)
    raise ValueError('Use DD/MM/AAAA.')


def formatar_data(valor):
    return date.fromisoformat(valor).strftime('%d/%m/%Y')
