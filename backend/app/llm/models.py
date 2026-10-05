"""Opções gratuitas conferidas no catálogo do OpenRouter em 04/10/2026."""

MODELOS_GRATUITOS = {
    'dots-studio/dots-3-note-preview:free': 'Dots3-Note Preview · gratuito',
    'nvidia/nemotron-3-super-120b-a12b:free': 'Nemotron 3 Super · gratuito',
}


def opcoes(config):
    if config.provider != 'openrouter':
        return [{'id': config.model, 'name': config.model}]
    modelos = dict(MODELOS_GRATUITOS)
    if config.model not in modelos:
        modelos[config.model] = ('Automático · gratuito' if config.model == 'openrouter/free'
                                 else config.model)
    return [{'id': identificador, 'name': nome} for identificador, nome in modelos.items()]
